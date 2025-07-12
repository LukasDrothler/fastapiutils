
from typing import Optional

from .auth_service import AuthService
from .user_queries import UserQueries
from .i18n_service import I18nService
from .user_validators import UserValidators
from .models import UpdateForgottenPassword, UserInDB, VerifyEmailRequest
from .mail_service import MailService
from .database_service import DatabaseService
from .verification_queries import VerificationQueries

from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status

def _check_verification_code(
        user: Optional[UserInDB],
        code: str,
        db_service: DatabaseService,
        i18n_service: I18nService,
        locale: str,
        allow_verified: bool = False
        ) -> UserInDB:
    """Check if verification code is valid, not used and not expired"""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=i18n_service.t("auth.user_not_found", locale),
        )

    verification_record = VerificationQueries.get_verification_code_by_user_id(
        user_id=user.id, db_service=db_service
        )
    
    if not verification_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=i18n_service.t("auth.no_verification_code", locale),
        )
    
    # Check if code matches
    if verification_record.value != code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=i18n_service.t("auth.invalid_verification_code", locale),
        )
    
    # Check if code has already been used
    if not allow_verified and verification_record.verified_at is not None:
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
        db_service: DatabaseService, 
        i18n_service: I18nService,
        mail_service: MailService,
        locale: str, 
        ) -> bool:
    """Verify user email using 6-digit code"""

    user = UserQueries.get_user_by_email(verify_request.email, db_service=db_service)
    _check_verification_code(
        user=user,
        code=verify_request.code,
        locale=locale,
        db_service=db_service,
        i18n_service=i18n_service
    )

    VerificationQueries.mark_verification_code_as_used(user_id=user.id, db_service=db_service)
    VerificationQueries.update_user_email_verified_status(user_id=user.id, verified=True, db_service=db_service)

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


def resend_verification_code(
        email: str,
        db_service: DatabaseService,
        mail_service: MailService,
        i18n_service: I18nService,
        locale: str,
    ) -> dict:

    user = UserQueries.get_user_by_email(email=email, db_service=db_service)
    verification_code = VerificationQueries.create_verification_code(
        user=None,
        email=email,
        locale=locale,
        db_service=db_service,
        i18n_service=i18n_service
        )

    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=i18n_service.t("auth.email_already_verified", locale)
        )

    try:
        # Generate new verification code
        mail_service.send_email_plain_text(
            content=i18n_service.t("auth.email_verification_content", locale, 
                                    username=user.username, 
                                    verification_code=verification_code),
            subject=i18n_service.t("auth.email_verification_subject", locale),
            recipient=email
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=i18n_service.t("auth.email_sending_failed", locale, error=str(e))
        )

    return {"msg": i18n_service.t("auth.verification_code_resent", locale)}


def send_forgot_password_verification(
        email: str,
        db_service: DatabaseService,
        mail_service: MailService,
        i18n_service: I18nService,
        locale: str,
    ) -> dict:

    user = UserQueries.get_user_by_email(email=email, db_service=db_service)
    verification_code = VerificationQueries.create_verification_code(
        user=None,
        email=email,
        locale=locale,
        db_service=db_service,
        i18n_service=i18n_service
        )

    try:
        # Generate new verification code
        mail_service.send_email_plain_text(
            content=i18n_service.t("auth.forgot_password_verification_content", locale, 
                                    username=user.username, 
                                    verification_code=verification_code),
            subject=i18n_service.t("auth.forgot_password_verification_subject", locale),
            recipient=email
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=i18n_service.t("auth.email_sending_failed", locale, error=str(e))
        )

    return {"msg": i18n_service.t("auth.forgot_password_verification_code_sent", locale)}


def send_email_change_verification(
        user: UserInDB,
        new_email: str,
        db_service: DatabaseService,
        mail_service: MailService, 
        i18n_service: I18nService,
        locale: str, 
        ) -> dict:
    """Initiate email change process by sending verification code to new email"""

    # Check if new email is the same as current email
    if user.email.lower() == new_email.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=i18n_service.t("auth.email_same_as_current", locale)
        )

    UserValidators.validate_email_format(new_email, locale, i18n_service)
    UserValidators.validate_email_unique(
            email=new_email,
            locale=locale, 
            db_service=db_service, 
            i18n_service=i18n_service
        )
    verification_code = VerificationQueries.create_verification_code(
        user=user,
        email=new_email,
        locale=locale,
        db_service=db_service,
        i18n_service=i18n_service
    )
    
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


def verify_user_email_change(
        user: UserInDB,
        verify_request: VerifyEmailRequest,
        db_service: DatabaseService,
        i18n_service: I18nService,
        locale: str,
        ) -> dict:
    """Verify email change using 6-digit code and update user's email"""

    _check_verification_code(
        user=user,
        code=verify_request.code,
        locale=locale,
        db_service=db_service,
        i18n_service=i18n_service
    )
    
    UserValidators.validate_email_format(email=verify_request.email, locale=locale, i18n_service=i18n_service)
    UserValidators.validate_email_unique(
            email=verify_request.email,
            locale=locale, 
            db_service=db_service, 
            i18n_service=i18n_service
        )
    VerificationQueries.update_user_email(user_id=user.id, new_email=verify_request.email, db_service=db_service)
    VerificationQueries.mark_verification_code_as_used(user_id=user.id, db_service=db_service)
    
    return {"msg": i18n_service.t("auth.email_change_verified_successfully", locale)}


def verify_forgot_password_with_code(
        verify_request: VerifyEmailRequest,
        db_service: DatabaseService,
        i18n_service: I18nService,
        locale: str,
        ) -> dict:
    """Verify forgot password request using 6-digit code"""

    user = UserQueries.get_user_by_email(email=verify_request.email, db_service=db_service)
    _check_verification_code(
        user=user,
        code=verify_request.code,
        locale=locale,
        db_service=db_service,
        i18n_service=i18n_service
    )

    VerificationQueries.mark_verification_code_as_used(user_id=user.id, db_service=db_service)
    
    return {"msg": i18n_service.t("auth.forgot_password_verified_successfully", locale)}


def update_forgotten_password_with_code(
        update_forgotten_password: UpdateForgottenPassword,
        auth_service: AuthService,
        db_service: DatabaseService,
        i18n_service: I18nService,
        locale: str,
    ) -> dict:
    """Update forgotten password using verification code"""

    user = UserQueries.get_user_by_email(email=update_forgotten_password.email, db_service=db_service)
    _check_verification_code(
        user=user,
        code=update_forgotten_password.verification_code,
        locale=locale,
        db_service=db_service,
        i18n_service=i18n_service,
        allow_verified=True
    )

    auth_service.update_password(
        user_id=user.id,
        new_password=update_forgotten_password.new_password,
        db_service=db_service,
        i18n_service=i18n_service,
        locale=locale
    )
    
    return {"msg": i18n_service.t("auth.forgotten_password_updated_successfully", locale)}