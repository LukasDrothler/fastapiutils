from fastapi import APIRouter, Depends, Request, Header

from ..database_service import DatabaseService
from ..stripe_service import StripeService
from ..i18n_service import I18nService
from ..dependencies import CurrentActiveUser, get_database_service, get_i18n_service, get_stripe_service

import logging

logger = logging.getLogger('uvicorn.error')

"""Create user management router with dependency injection"""
router = APIRouter()

@router.post("/stripe-webhook", tags=["stripe"])
async def stripe_webhook_received(
    request: Request,
    stripe_signature=Header(None),
    i18n_service: I18nService = Depends(get_i18n_service),
    db_service: DatabaseService = Depends(get_database_service),
    stripe_service: StripeService = Depends(get_stripe_service),
):
    locale = i18n_service.extract_locale_from_request(request)
    return await stripe_service.handle_webhook_event(
        request=request,
        i18n_service=i18n_service,
        db_service=db_service,
        stripe_signature=stripe_signature,
        locale=locale
        )

@router.post("/create-customer-portal-session", tags=["stripe"])
async def create_customer_portal_session(
    request: Request,
    current_user: CurrentActiveUser,
    stripe_service: StripeService = Depends(get_stripe_service),
    i18n_service: I18nService = Depends(get_i18n_service),
):
    locale = i18n_service.extract_locale_from_request(request)
    return await stripe_service.create_customer_portal_session(
        customer_id=current_user.stripe_customer_id,
        i18n_service=i18n_service,
        locale=locale
    )