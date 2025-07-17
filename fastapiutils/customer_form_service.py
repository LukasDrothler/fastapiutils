import logging

from fastapi import HTTPException, status

from .i18n_service import I18nService
from .database_service import DatabaseService
from .models import CreateCancellation, CreateFeedback

logger = logging.getLogger('uvicorn.error')


class CustomerFormService:
    """Customer service for managing customer-related operations"""

    def create_cancellation(
            self,
            cancellation_data: CreateCancellation,
            db_service: DatabaseService,
            i18n_service: I18nService,
            locale: str = "en"
            ) -> None:
        """Create a new cancellation in the database"""
        try:
            db_service.execute_modification_query(
            "INSERT INTO cancellation (email, name, last_name, address, town, town_number, is_unordinary, is_archived, reason, last_invoice_number, termination_date) VALUES (%s, %s, %s, %s, %s, %s, %s, 0, %s, %s, %s)",
            (
                cancellation_data.email,
                cancellation_data.name,
                cancellation_data.last_name,
                cancellation_data.address,
                cancellation_data.town,
                cancellation_data.town_number,
                cancellation_data.is_unordinary,
                cancellation_data.reason,
                cancellation_data.last_invoice_number,
                cancellation_data.termination_date
            )
        )
        except Exception as e:
            logger.error(f"Error creating cancellation: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=i18n_service.t("api.customer_form.cancellation_creation_failed", locale)
            )
        return i18n_service.t("api.customer_form.cancellation_created", locale)


    def create_feedback(
            self,
            feedback_data: CreateFeedback,
            db_service: DatabaseService,
            i18n_service: I18nService,
            locale: str = "en"
            ) -> None:
        """Create a new feedback entry in the database"""
        try:
            db_service.execute_modification_query(
                "INSERT INTO feedback (email, text) VALUES (%s, %s)",
                (feedback_data.email, feedback_data.text)
            )
        except Exception as e:
            logger.error(f"Error creating feedback: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=i18n_service.t("api.customer_form.feedback_creation_failed", locale)
            )
        return i18n_service.t("api.customer_form.feedback_created", locale)


    def archive_cancellation(
            self,
            cancellation_id: int,
            db_service: DatabaseService,
            i18n_service: I18nService,
            locale: str = "en"
            ) -> None:
        """Archive a cancellation by its ID"""
        try:
            db_service.execute_modification_query(
                "UPDATE cancellation SET is_archived = 1 WHERE id = %s",
                (cancellation_id,)
            )
        except Exception as e:
            logger.error(f"Error archiving cancellation: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=i18n_service.t("api.customer_form.cancellation_archiving_failed", locale)
            )
        return i18n_service.t("api.customer_form.cancellation_archived", locale)


    def archive_feedback(
            self,
            feedback_id: int,
            db_service: DatabaseService,
            i18n_service: I18nService,
            locale: str = "en"
            ) -> None:
        """Archive a feedback entry by its ID"""
        try:
            db_service.execute_modification_query(
                "UPDATE feedback SET is_archived = 1 WHERE id = %s",
                (feedback_id,)
            )
        except Exception as e:
            logger.error(f"Error archiving feedback: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=i18n_service.t("api.customer_form.feedback_archival_failed", locale)
            )
        return i18n_service.t("api.customer_form.feedback_archived", locale)
    
    
    def get_feedbacks(
            self,
            db_service: DatabaseService,
            i18n_service: I18nService,
            locale: str = "en"
            ):
        """Retrieve all feedback entries from the database"""
        try:
            return db_service.execute_query(
                "SELECT id, email, text FROM feedback WHERE is_archived = 0"
            )
        except Exception as e:
            logger.error(f"Error retrieving feedback: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=i18n_service.t("api.customer_form.feedback_retrieval_failed", locale)
            )


    def get_cancellations(
            self,
            db_service: DatabaseService,
            i18n_service: I18nService,
            locale: str = "en"
            ):
        """Retrieve all cancellation entries from the database"""
        try:
            return db_service.execute_query(
                "SELECT id, email, name, last_name, address, town, town_number, is_unordinary, reason, last_invoice_number, termination_date FROM cancellation WHERE is_archived = 0"
            )
        except Exception as e:
            logger.error(f"Error retrieving cancellations: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=i18n_service.t("api.customer_form.cancellation_retrieval_failed", locale)
            )