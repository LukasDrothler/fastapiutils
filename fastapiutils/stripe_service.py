import logging
import os
import json
import stripe

from fastapi import HTTPException, status, Request, Header

from .user_queries import UserQueries
from .i18n_service import I18nService
from .database_service import DatabaseService

logger = logging.getLogger('uvicorn.error')


class StripeService:
    """Service for handling Stripe-related operations"""

    def __init__(self):
        """Initialize the Stripe service with environment variables"""
        self.is_active = False

        if "STRIPE_CONFIG_FILE" in os.environ:
            _config_file = os.environ["STRIPE_CONFIG_FILE"]
            logger.info(f"Using Stripe config file from environment variable 'STRIPE_CONFIG_FILE': {_config_file}")
            self.product_id_map = self.read_product_id_map(_config_file)

            if "STRIPE_SECRET_API_KEY" in os.environ:
                self.secret_key = os.environ["STRIPE_SECRET_API_KEY"]
                logger.info(f"Using Stripe secret key from environment variable 'STRIPE_SECRET_API_KEY'")

                if "STRIPE_SIGNING_SECRET" in os.environ:
                    self.signing_secret = os.environ["STRIPE_SIGNING_SECRET"]
                    logger.info(f"Using Stripe signing secret from environment variable 'STRIPE_SIGNING_SECRET'")

                    self.is_active = True
                    logger.info("Stripe service is active")

                else:
                    logger.warning("Environment variable 'STRIPE_SIGNING_SECRET' not found. Stripe service will not be active")
            else:
                logger.warning("Environment variable 'STRIPE_SECRET_API_KEY' not found. Stripe service will not be active")
        else:
            logger.warning("Environment variable 'STRIPE_CONFIG_FILE' not found. Stripe service will not be active")


    def read_product_id_map(self, config_file):
        """Read Stripe configuration from a JSON file"""
        try:
            with open(config_file, 'r') as file:
                config = json.load(file)
                product_map = config.get("product_id_to_premium_level", {})
                if not product_map:
                    logger.error(f"No product ID map found in {config_file}")
                    raise Exception(
                        f"No product ID map found in {config_file}. Please check your configuration."
                    )
                logger.info(f"Successfully loaded product ID map from {config_file}")
                return product_map
  
        except FileNotFoundError:
            logger.error(f"Stripe configuration file {config_file} not found")
            raise Exception(
                f"Stripe configuration file {config_file} not found. Please check your environment variables."
            )
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from Stripe configuration file {config_file}")
            raise Exception(
                f"Error decoding JSON from Stripe configuration file {config_file}. Please check the file format."
            )
        return None


    async def _get_constructed_event(
            self,
            request: Request,
            i18n_service: I18nService,
            stripe_signature = Header(None),
            locale: str = "en"
    ):
        if not self.is_active:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=i18n_service.t("api.stripe.webhook.service_not_active", locale)
            )
        
        _payload = await request.body()
        try:
            return stripe.Webhook.construct_event(
                payload=_payload,
                sig_header=stripe_signature,
                secret=self.signing_secret,
                api_key=self.secret_key
            )
        except Exception as e:
            logger.error(f"Failed to construct event: {e}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=i18n_service.t("api.stripe.webhook.invalid_event", locale)
            )
        
    async def handle_webhook_event(
            self,
            request: Request,
            i18n_service: I18nService,
            db_service: DatabaseService,
            stripe_signature: str = Header(None),
            locale: str = "en"
    ):
        """Handle incoming Stripe webhook events"""
        event = await self._get_constructed_event(
            request=request,
            i18n_service=i18n_service,
            stripe_signature=stripe_signature,
            locale=locale
            )
        
        try:
            _data = event["data"]["object"]
            _data_id = _data["id"]
        except KeyError:
            logger.error(f"Invalid event data")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=i18n_service.t("api.stripe.webhook.invalid_event", locale)
            )

        # Process the event based on its type
        if event['type'] == 'checkout.session.completed':
            return self._handle_checkout_session(
                data_id=_data_id,
                db_service=db_service,
                i18n_service=i18n_service,
                locale=locale
                )
        elif event['type'] == 'customer.subscription.deleted':
            return self._handle_subscription_deleted(
                data_id=_data_id,
                db_service=db_service,
                i18n_service=i18n_service,
                locale=locale
                )
        else:
            return {"detail": i18n_service.t("api.stripe.webhook.event_not_handled", locale, error=event['type'])}
        
    
    def _handle_checkout_session(
            self, 
            data_id: str,
            db_service: DatabaseService,
            i18n_service: I18nService,
            locale: str = "en"
            ):
        """Handle checkout session completed event"""
        session_data = stripe.checkout.Session.retrieve(
            data_id,
            expand=["line_items"],
            api_key=self.secret_key
            )
        
        try:
            user_email = session_data["customer_details"]["email"]
            user_id = session_data["client_reference_id"]
            stripe_customer_id = session_data["customer"]
            product_id = session_data["line_items"]["data"][0]["price"]["product"]
        except KeyError:
            logger.error(f"Invalid session data for session '{data_id}'")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid session data"
            )

        if not user_email:
            logger.error(f"User email not found in session data for session '{data_id}'")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=i18n_service.t("api.stripe.webhook.invalid_event", locale)
            )
        
        if not user_id:
            logger.error(f"User ID not found in session data for session '{data_id}'")
            logger.error("Make sure to set the user id as 'client_reference_id' when creating the checkout session")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=i18n_service.t("api.stripe.webhook.invalid_event", locale)
            )
        
        if not stripe_customer_id:
            logger.error(f"Stripe customer ID not found in session data for session '{data_id}'")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=i18n_service.t("api.stripe.webhook.invalid_event", locale)
            )

        new_premium_level = self.product_id_map.get(product_id, None)
        if new_premium_level is None:
            logger.error(f"Invalid product ID: {product_id}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=i18n_service.t(
                    key="api.stripe.webhook.invalid_product_id",
                    locale=locale,
                    product_id=product_id
                )
            )

        user = UserQueries.get_user_by_id(user_id=user_id, db_service=db_service)
        if user is None:
            ## This case can only occur, if someone opens the paymentlink without being registered
            logger.error(f"User with id '{user_id}' not found in database")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=i18n_service.t(
                    key="api.auth.user_management.user_not_found",
                    locale=locale
                )
            )

        if user.premium_level == new_premium_level:
            logger.error(f"User with id '{user_id}' already has premium access")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=i18n_service.t(
                    key="api.stripe.webhook.user_already_has_premium",
                    locale=locale,
                    user_id=user_id,
                    new_premium_level=new_premium_level
                )
            )
        
        msg = UserQueries.update_user_premium_level(
            user_id=user_id,
            new_premium_level=new_premium_level,
            stripe_customer_id=stripe_customer_id,
            db_service=db_service,
            i18n_service=i18n_service,
            locale=locale
        )

        # TODO: Send email to user about successful premium upgrade
        return msg
    

    def _handle_subscription_deleted(
            self, 
            data_id: str,
            db_service: DatabaseService,
            i18n_service: I18nService,
            locale: str = "en"
            ):
        """Handle subscription deletion event"""
        subscription_data = stripe.Subscription.retrieve(data_id, api_key=self.secret_key)
        try:
            product_id = subscription_data["items"]["data"][0]["price"]["product"]
            stripe_customer_id = subscription_data["customer"]
        except KeyError:
            logger.error(f"Invalid subscription data for subscription '{data_id}'")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=i18n_service.t("api.stripe.webhook.invalid_event", locale)
            )
        
        if product_id not in self.product_id_map:
            logger.error(f"Invalid product ID: {product_id}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=i18n_service.t("api.stripe.webhook.invalid_product_id", locale)
            )

        if stripe_customer_id is None:
            logger.error(f"Stripe customer ID not found in subscription data for subscription '{data_id}'")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=i18n_service.t("api.stripe.webhook.invalid_event", locale)
            )

        user = UserQueries.get_user_by_stripe_customer_id(
            stripe_customer_id=stripe_customer_id,
            db_service=db_service
            )
        if user is None:
            logger.error(f"No user found with stripe_customer_id '{stripe_customer_id}'")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=i18n_service.t("api.auth.user_management.user_not_found", locale)
            )
 
        msg = UserQueries.update_user_premium_level(
            user_id=user.id,
            new_premium_level=0,
            stripe_customer_id=user.stripe_customer_id,
            db_service=db_service,
            i18n_service=i18n_service,
            locale=locale
        )

        # TODO: Send email to user about successful premium downgrade
        return msg


    def create_customer_portal_session(
            self,
            customer_id: str,
            i18n_service: I18nService,
            locale: str = "en"
    ):
        """Create a customer portal session for managing subscriptions"""
        if not self.is_active:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=i18n_service.t("api.stripe.webhook.service_not_active", locale)
            )
        
        try:
        ## https://docs.stripe.com/api/customer_portal/sessions/create
            return stripe.billing_portal.Session.create(
                customer=customer_id,
                locale=locale,
                api_key=self.secret_key
            )
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create customer portal session: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=i18n_service.t("api.stripe.portal.session_creation_failed", locale, error=str(e))
            )
