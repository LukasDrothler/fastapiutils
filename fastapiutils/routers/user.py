from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..user_queries import UserQueries
from ..auth_service import AuthService
from ..i18n_service import I18nService
from ..database_service import DatabaseService
from ..email_verification import resend_verification_code, send_email_change_verification, send_forgot_password_verification, update_forgotten_password_with_code, verify_forgot_password_with_code, verify_user_email_change, verify_user_email_with_code
from ..mail_service import MailService
from ..models import CreateUser, SendVerificationRequest, UpdateForgottenPassword, User, UserInDBNoPassword, VerifyEmailRequest, UpdateUser, UpdatePassword, VerifyEmailRequest
from ..dependencies import CurrentAdminUser, get_auth_service, get_database_service, get_mail_service, get_i18n_service, CurrentActiveUser

import logging

logger = logging.getLogger('uvicorn.error')

"""Create user management router with dependency injection"""
router = APIRouter()


@router.get("/user/me", response_model=User, tags=["user-information"])
async def read_users_me(current_user: CurrentActiveUser):
    return current_user


@router.post("/user/register", status_code=201, tags=["user-registration"])
async def create_new_user(
    user: CreateUser,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    db_service: DatabaseService = Depends(get_database_service),
    mail_service: MailService = Depends(get_mail_service),
    i18n_service: I18nService = Depends(get_i18n_service),
):
    locale = i18n_service.extract_locale_from_request(request)
    return auth_service.register_new_user(
        user=user,
        locale=locale,
        db_service=db_service,
        i18n_service=i18n_service,
        mail_service=mail_service
        )


@router.post("/user/verify-email", status_code=200, tags=["user-registration"])
async def verify_user_email(
    verify_request: VerifyEmailRequest,
    request: Request,
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service),
    mail_service: MailService = Depends(get_mail_service),
):
    locale = i18n_service.extract_locale_from_request(request)
    return verify_user_email_with_code(
        verify_request=verify_request,
        locale=locale,
        db_service=db_service, 
        i18n_service=i18n_service,
        mail_service=mail_service
        )
    

@router.post("/user/resend-verification", status_code=200, tags=["user-registration"])
async def send_new_verification_code(
    send_verification_request: SendVerificationRequest,
    request: Request,
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service),
    mail_service: MailService = Depends(get_mail_service),
):
    locale = i18n_service.extract_locale_from_request(request)
    return resend_verification_code(
        email=send_verification_request.email,
        locale=locale,
        db_service=db_service,
        mail_service=mail_service, 
        i18n_service=i18n_service
        )


@router.put("/user/me", status_code=200, tags=["user-information"])
async def update_user_info(
    user_update: UpdateUser,
    request: Request,
    current_user: CurrentActiveUser,
    auth_service: AuthService = Depends(get_auth_service),
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service),
):
    """Update current user's information"""
    locale = i18n_service.extract_locale_from_request(request)
    return auth_service.update_user(
        user_id=current_user.id, 
        user_update=user_update,
        locale=locale,
        db_service=db_service,
        i18n_service=i18n_service
        )


@router.put("/user/me/password", status_code=200, tags=["user-information"])
async def change_user_password(
    password_update: UpdatePassword,
    request: Request,
    current_user: CurrentActiveUser,
    auth_service: AuthService = Depends(get_auth_service),
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service),
):
    """Update current user's password"""
    locale = i18n_service.extract_locale_from_request(request)
    return auth_service.update_password(
        user_id=current_user.id,
        password_update=password_update,
        locale=locale,
        db_service=db_service,
        i18n_service=i18n_service
        )


@router.post("/user/me/email/change", status_code=200, tags=["user-information"])
async def request_user_email_change(
    send_verification_request: SendVerificationRequest,
    request: Request,
    current_user: CurrentActiveUser,
    db_service: DatabaseService = Depends(get_database_service),
    mail_service: MailService = Depends(get_mail_service),
    i18n_service: I18nService = Depends(get_i18n_service),
):
    """Initiate email change process - sends verification code to new email"""
    locale = i18n_service.extract_locale_from_request(request)

    return send_email_change_verification(
        user=current_user,
        new_email=send_verification_request.email,
        locale=locale,
        db_service=db_service,
        mail_service=mail_service,
        i18n_service=i18n_service
        )


@router.post("/user/me/email/verify", status_code=200, tags=["user-information"])
async def user_email_change_verification(
    verify_request: VerifyEmailRequest,
    request: Request,
    current_user: CurrentActiveUser,
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service),
):
    """Verify email change with 6-digit code and update user's email"""
    locale = i18n_service.extract_locale_from_request(request)
    return verify_user_email_change(
        user=current_user,
        verify_request=verify_request,
        locale=locale,
        db_service=db_service,
        i18n_service=i18n_service
        )


@router.post("/user/forgot-password/request", status_code=200, tags=["user-password-recovery"])
async def request_forgot_password(
    send_verification_request: SendVerificationRequest,
    request: Request,
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service),
    mail_service: MailService = Depends(get_mail_service),
):
    locale = i18n_service.extract_locale_from_request(request)
    return send_forgot_password_verification(
        email=send_verification_request.email,
        locale=locale,
        db_service=db_service,
        mail_service=mail_service, 
        i18n_service=i18n_service
        )


@router.post("/user/forgot-password/verify", status_code=200, tags=["user-password-recovery"])
async def forgot_password_verification(
    verify_request: VerifyEmailRequest,
    request: Request,
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service),
):
    """Verify email change with 6-digit code and update user's email"""
    locale = i18n_service.extract_locale_from_request(request)
    return verify_forgot_password_with_code(
        verify_request=verify_request,
        locale=locale,
        db_service=db_service,
        i18n_service=i18n_service
        )


@router.post("/user/forgot-password/change", status_code=200, tags=["user-password-recovery"])
async def change_forgotten_password(
    update_forgotten_password: UpdateForgottenPassword,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service),
):
    """Verify email change with 6-digit code and update user's email"""
    locale = i18n_service.extract_locale_from_request(request)
    return update_forgotten_password_with_code(
        update_forgotten_password=update_forgotten_password,
        locale=locale,
        auth_service=auth_service,
        db_service=db_service,
        i18n_service=i18n_service
        )


@router.get("/user/{user_id}/username", response_model=str, tags=["user-information"])
async def get_username_by_id(
    user_id: str,
    request: Request,
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service),
):
    """Get username by user ID"""
    locale = i18n_service.extract_locale_from_request(request)
    return UserQueries.get_username_by_id(
        user_id=user_id,
        db_service=db_service,
        i18n_service=i18n_service,
        locale=locale
    )


@router.post("/user/id-to-name-map", response_model=dict, tags=["user-information"])
async def get_user_ids_to_names(
    user_ids: list[str],
    request: Request,
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service),
):
    """Get user names by their IDs"""
    locale = i18n_service.extract_locale_from_request(request)
    return UserQueries.get_user_ids_to_names(
        user_ids=user_ids,
        db_service=db_service,
        i18n_service=i18n_service,
        locale=locale
    )


@router.get("/user/all", response_model=list[UserInDBNoPassword], tags=["user-management"])
async def get_all_users(
    current_admin: CurrentAdminUser,
    request: Request,
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service),
):
    """Get all users from the database"""
    locale = i18n_service.extract_locale_from_request(request)
    if not current_admin.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return UserQueries.get_all_users(
        db_service=db_service,
        i18n_service=i18n_service,
        locale=locale
    )


@router.delete("/user/{user_id}", status_code=200, tags=["user-management"])
async def delete_user(
    user_id: str,
    current_admin: CurrentAdminUser,
    request: Request,
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service),
):
    """Delete a user by ID"""
    locale = i18n_service.extract_locale_from_request(request)
    if not current_admin.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    return UserQueries.delete_user(
        user_id=user_id,
        db_service=db_service,
        i18n_service=i18n_service,
        locale=locale
    )