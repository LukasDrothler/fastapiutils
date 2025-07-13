
from typing import Optional
from datetime import datetime, timezone, timedelta

from fastapi import HTTPException, status

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
            detail=i18n_service.t("api.auth.user_management.user_not_found", locale),
        )

    verification_record = VerificationQueries.get_verification_code_by_user_id(
        user_id=user.id, db_service=db_service
        )
    
    if not verification_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=i18n_service.t("api.auth.verification.no_verification_code", locale),
        )
    
    # Check if code matches
    if verification_record.value != code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=i18n_service.t("api.auth.verification.invalid_verification_code", locale),
        )
    
    # Check if code has already been used
    if not allow_verified and verification_record.verified_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=i18n_service.t("api.auth.verification.verification_code_already_used", locale),
        )
    
    # Check if code is expired (24 hours)
    time_diff = datetime.now(timezone.utc) - verification_record.created_at.replace(tzinfo=timezone.utc)
    if time_diff >= timedelta(hours=24):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=i18n_service.t("api.auth.verification.verification_code_expired", locale),
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
            content=i18n_service.t("email.fallback_content.email_verified", locale),
            subject=i18n_service.t("email.subjects.email_verified", locale),
            recipient=verify_request.email,
            i18n_service=i18n_service,
            locale=locale
        )
    except Exception:
        # If email sending fails, we still mark the email as verified
        pass
    
    return {"msg": i18n_service.t("email.subjects.email_verified", locale)}


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
            detail=i18n_service.t("api.auth.verification.email_already_verified", locale)
        )

    mail_service.send_email_verification_mail(
            recipient=user.email,
            username=user.username,
            verification_code=verification_code,
            i18n_service=i18n_service,
            locale=locale
        )

    return {"msg": i18n_service.t("api.auth.verification.verification_code_resent", locale)}


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
        # Get company name from locale configuration
        config = mail_service._load_template_config("forgot_password_verification", i18n_service, locale)
        app_name = config.get("defaults", {}).get("app_name", "YourApp")
        contact_email = config.get("defaults", {}).get("contact_email", "support@yourapp.com")
        
        # Use template system for forgot password verification
        mail_service.send_email_with_template(
            template_name="forgot_password_verification",
            variables={
                "username": user.username,
                "verification_code": verification_code,
                "app_name": app_name,
                "contact_email": contact_email
            },
            subject=i18n_service.t("email.subjects.forgot_password_verification", locale),
            recipient=email,
            locale=locale,
            plain_text_content=i18n_service.t("email.fallback_content.forgot_password_verification", locale, 
                                            username=user.username, 
                                            verification_code=verification_code),
            i18n_service=i18n_service
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=i18n_service.t("api.email.email_sending_failed", locale, error=str(e))
        )

    return {"msg": i18n_service.t("api.auth.forgot_password.forgot_password_verification_code_sent", locale)}


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
            detail=i18n_service.t("api.auth.validation.email_same_as_current", locale)
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
        # Get company name from locale configuration
        config = mail_service._load_template_config("email_change_verification", i18n_service, locale)
        app_name = config.get("defaults", {}).get("app_name", "YourApp")
        contact_email = config.get("defaults", {}).get("contact_email", "support@yourapp.com")
        
        # Use template system for email change verification
        mail_service.send_email_with_template(
            template_name="email_change_verification",
            variables={
                "username": user.username,
                "verification_code": verification_code,
                "app_name": app_name,
                "contact_email": contact_email
            },
            subject=i18n_service.t("email.subjects.email_change_verification", locale),
            recipient=new_email,
            locale=locale,
            plain_text_content=i18n_service.t("email.fallback_content.email_change_verification", locale, 
                                            username=user.username, 
                                            verification_code=verification_code),
            i18n_service=i18n_service
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=i18n_service.t("api.email.email_sending_failed", locale, error=str(e))
        )
    
    return {"msg": i18n_service.t("api.auth.email_change.email_change_verification_sent", locale)}


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
    
    return {"msg": i18n_service.t("api.auth.email_change.email_change_verified_successfully", locale)}


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
    
    return {"msg": i18n_service.t("api.auth.password_management.forgot_password_verified_successfully", locale)}


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
    
    return {"msg": i18n_service.t("api.auth.password_management.forgotten_password_updated_successfully", locale)}