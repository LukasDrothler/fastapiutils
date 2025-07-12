from fastapi import APIRouter, Depends, Request

from ..auth_service import AuthService
from ..i18n_service import I18nService
from ..database_service import DatabaseService
from ..email_verification import resend_verification_code, send_email_change_verification, verify_user_email_change, verify_user_email_with_code
from ..mail_service import MailService
from ..models import CreateUser, ResendVerificationRequest, User, UserInDB, VerifyEmailRequest, UpdateUser, UpdatePassword, UpdateMail, VerifyEmailRequest
from ..dependencies import get_auth_service, get_database_service, get_mail_service, get_i18n_service, CurrentActiveUser

import logging

logger = logging.getLogger('uvicorn.error')

"""Create user management router with dependency injection"""
router = APIRouter()


@router.get("/user/me", response_model=User, tags=["users"])
async def read_users_me(current_user: CurrentActiveUser):
    return current_user


@router.post("/user/register", status_code=201, tags=["users"])
async def create_new_user(
    user: CreateUser,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    db_service: DatabaseService = Depends(get_database_service),
    mail_service: MailService = Depends(get_mail_service),
    i18n_service: I18nService = Depends(get_i18n_service),
):
    locale = i18n_service.extract_locale_from_header(request.headers.get("accept-language"))
    return auth_service.register_new_user(
        user=user,
        locale=locale,
        db_service=db_service,
        i18n_service=i18n_service,
        mail_service=mail_service
        )


@router.post("/user/verify-email", status_code=200, tags=["users"])
async def verify_user_email(
    verify_request: VerifyEmailRequest,
    request: Request,
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service),
    mail_service: MailService = Depends(get_mail_service),
):
    locale = i18n_service.extract_locale_from_header(request.headers.get("accept-language"))
    return verify_user_email_with_code(
        verify_request=verify_request,
        locale=locale,
        db_service=db_service, 
        i18n_service=i18n_service,
        mail_service=mail_service
        )
    

@router.post("/user/resend-verification", status_code=200, tags=["users"])
async def send_new_verification_code(
    resend_request: ResendVerificationRequest,
    request: Request,
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service),
    mail_service: MailService = Depends(get_mail_service),
):
    locale = i18n_service.extract_locale_from_header(request.headers.get("accept-language"))
    return resend_verification_code(
        email=resend_request.email,
        locale=locale,
        db_service=db_service,
        mail_service=mail_service, 
        i18n_service=i18n_service
        )


@router.put("/user/me", status_code=200, tags=["users"])
async def update_user_info(
    user_update: UpdateUser,
    request: Request,
    current_user: CurrentActiveUser,
    auth_service: AuthService = Depends(get_auth_service),
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service),
):
    """Update current user's information"""
    locale = i18n_service.extract_locale_from_header(request.headers.get("accept-language"))
    return auth_service.update_user(
        user_id=current_user.id, 
        user_update=user_update,
        locale=locale,
        db_service=db_service,
        i18n_service=i18n_service
        )


@router.put("/user/me/password", status_code=200, tags=["users"])
async def update_user_password(
    password_update: UpdatePassword,
    request: Request,
    current_user: CurrentActiveUser,
    auth_service: AuthService = Depends(get_auth_service),
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service),
):
    """Update current user's password"""
    locale = i18n_service.extract_locale_from_header(request.headers.get("accept-language"))
    return auth_service.update_password(
        user_id=current_user.id,
        password_update=password_update,
        locale=locale,
        db_service=db_service,
        i18n_service=i18n_service
        )


@router.post("/user/me/email/change", status_code=200, tags=["users"])
async def request_user_email_change(
    email_update: UpdateMail,
    request: Request,
    current_user: CurrentActiveUser,
    db_service: DatabaseService = Depends(get_database_service),
    mail_service: MailService = Depends(get_mail_service),
    i18n_service: I18nService = Depends(get_i18n_service),
):
    """Initiate email change process - sends verification code to new email"""
    locale = i18n_service.extract_locale_from_header(request.headers.get("accept-language"))

    return send_email_change_verification(
        user=current_user,
        new_email=email_update.email,
        locale=locale,
        db_service=db_service,
        mail_service=mail_service,
        i18n_service=i18n_service
        )


@router.post("/user/me/email/verify", status_code=200, tags=["users"])
async def user_email_change_verification(
    verify_request: VerifyEmailRequest,
    request: Request,
    current_user: CurrentActiveUser,
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service),
):
    """Verify email change with 6-digit code and update user's email"""
    locale = i18n_service.extract_locale_from_header(request.headers.get("accept-language"))
    return verify_user_email_change(
        user=current_user,
        verify_request=verify_request,
        locale=locale,
        db_service=db_service,
        i18n_service=i18n_service
        )