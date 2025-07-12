
from .user_queries import UserQueries
from .auth_service import AuthService
from .i18n_service import I18nService
from .user_validators import UserValidators
from .models import UserInDB, VerifyEmailRequest
from .mail_service import MailService
from .database_service import DatabaseService
from .verification_queries import VerificationQueries

from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status

def _check_verification_code(
        user_id: str,
        verify_request: VerifyEmailRequest,
        locale: str = "en", 
        db_service: DatabaseService = None,
        i18n_service: I18nService = None
        ) -> UserInDB:
    """Check if verification code is valid, not used and not expired"""
    verification_record = VerificationQueries.get_verification_code_by_user_id(
        user_id=user_id, db_service=db_service
        )
    
    if not verification_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=i18n_service.t("auth.no_verification_code", locale),
        )
    
    # Check if code matches
    if verification_record.value != verify_request.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=i18n_service.t("auth.invalid_verification_code", locale),
        )
    
    # Check if code has already been used
    if verification_record.verified_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=i18n_service.t("auth.verification_code_already_used", locale),
        )
    
    # Check if code is expired (24 hours)
    time_diff = datetime.now(timezone.utc) - verification_record.created_at.replace(tzinfo=timezone.utc)
    if time_diff >= timedelta(hours=24):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=i18n_service.t("auth.verification_code_expired", locale),
        )
    
    return None


def verify_user_email_with_code(
        verify_request: VerifyEmailRequest, 
        locale: str = "en", 
        db_service: DatabaseService = None, 
        i18n_service = None,
        mail_service: MailService = None
        ) -> bool:
    """Verify user email using 6-digit code"""

    user = UserQueries.get_user_by_email(verify_request.email, db_service=db_service)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=i18n_service.t("auth.user_not_found", locale),
        )
    
    _check_verification_code(
        user_id=user.id,
        verify_request=verify_request,
        locale=locale,
        db_service=db_service,
        i18n_service=i18n_service
    )

    VerificationQueries.mark_verification_code_as_used(user.id, db_service=db_service)
    VerificationQueries.update_user_email_verified_status(user.id, True, db_service=db_service)

    # Send confirmation email
    try:
        mail_service.send_email_plain_text(
            content=i18n_service.t("auth.email_verified_content", locale),
            subject=i18n_service.t("auth.email_verified_subject", locale),
            recipient=verify_request.email
        )
    except Exception:
        # If email sending fails, we still mark the email as verified
        pass
    
    return {"msg": i18n_service.t("auth.email_verified_subject", locale)}


def send_verification_code(
        email: str, locale: str = "en", 
        db_service: DatabaseService = None, 
        mail_service: MailService = None, 
        i18n_service = None
        ) -> dict:
    """Resend verification code if 1 minute has passed"""
    user = UserQueries.get_user_by_email(email, db_service=db_service)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=i18n_service.t("auth.user_not_found", locale),
        )
    
    # Check if user can resend
    if not VerificationQueries.can_send_verification(user.id, db_service=db_service):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=i18n_service.t("auth.resend_cooldown", locale),
        )
    
    try:
        # Generate new verification code
        verification_code = VerificationQueries.create_verification_code(user.id, db_service=db_service)
        
        mail_service.send_email_plain_text(
            content=i18n_service.t("auth.email_verification_content", locale, 
                                    username=user.username, 
                                    verification_code=verification_code),
            subject=i18n_service.t("auth.email_verification_subject", locale),
            recipient=user.email
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=i18n_service.t("auth.email_sending_failed", locale, error=str(e))
        )

    return {"msg": i18n_service.t("auth.verification_code_resent", locale)}


def send_email_change_verification(user: UserInDB, new_email: str, locale: str = "en", 
                         db_service: DatabaseService = None, mail_service: MailService = None, 
                         i18n_service: I18nService = None) -> dict:
    """Initiate email change process by sending verification code to new email"""

    # Check if new email is the same as current email
    if user.email.lower() == new_email.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=i18n_service.t("auth.email_same_as_current", locale)
        )

    UserValidators.validate_email_format(new_email, locale, i18n_service)
    UserValidators.validate_email_unique(new_email, user.id, locale, db_service, i18n_service)
    verification_code = VerificationQueries.create_verification_code(user.id, db_service=db_service)
    
    # Send verification email to new email address
    try:
        mail_service.send_email_plain_text(
            content=i18n_service.t("auth.email_change_verification_content", locale, 
                                    username=user.username, 
                                    verification_code=verification_code),
            subject=i18n_service.t("auth.email_change_verification_subject", locale),
            recipient=new_email
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=i18n_service.t("auth.email_sending_failed", locale, error=str(e))
        )
    
    return {"msg": i18n_service.t("auth.email_change_verification_sent", locale)}


def verify_user_email_change(user: UserInDB, verify_request: VerifyEmailRequest, locale: str = "en", 
                       db_service: DatabaseService = None, i18n_service: I18nService = None) -> dict:
    """Verify email change using 6-digit code and update user's email"""

    _check_verification_code(
        user_id=user.id,
        verify_request=verify_request,
        locale=locale,
        db_service=db_service,
        i18n_service=i18n_service
    )
    
    UserValidators.validate_email_format(verify_request.email, locale, i18n_service)
    UserValidators.validate_email_unique(verify_request.email, user.id, locale, db_service, i18n_service)
    VerificationQueries.update_user_email(user.id, verify_request.email, db_service=db_service)
    VerificationQueries.mark_verification_code_as_used(user.id, db_service=db_service)
    
    return {"msg": i18n_service.t("auth.email_change_verified_successfully", locale)}