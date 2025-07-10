from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..auth_service import AuthService
from ..i18n_service import I18nService
from ..database_service import DatabaseService
from ..email_verification import resend_verification_code, verify_user_email_with_code
from ..mail_service import MailService
from ..models import CreateUser, User, VerifyEmailRequest, UpdateUser, UpdatePassword
from ..dependencies import get_auth_service, get_database_service, get_mail_service, get_i18n_service, CurrentActiveUser

import logging

logger = logging.getLogger('uvicorn.error')

"""Create user management router with dependency injection"""
router = APIRouter()


@router.get("/user/me", response_model=User, tags=["users"])
async def read_users_me(current_user: CurrentActiveUser):
    return current_user


@router.post("/user/register", status_code=201, tags=["users"])
async def create_user(
    user: CreateUser,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    db_service: DatabaseService = Depends(get_database_service),
    mail_service: MailService = Depends(get_mail_service),
    i18n_service: I18nService = Depends(get_i18n_service),
):
    locale = i18n_service.extract_locale_from_header(request.headers.get("accept-language"))
    return auth_service.create_user(user, locale, db_service=db_service, i18n_service=i18n_service, mail_service=mail_service)


@router.post("/user/verify-email/{user_id}", status_code=200, tags=["users"])
async def verify_user_email(
    user_id: str,
    verify_request: VerifyEmailRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service),
    mail_service: MailService = Depends(get_mail_service),
):
    locale = i18n_service.extract_locale_from_header(request.headers.get("accept-language"))
    
    # Verify the code
    verify_user_email_with_code(verify_request.code, user_id, locale, 
                                db_service=db_service, i18n_service=i18n_service)
    
    # Get updated user
    user = auth_service.get_user(uid=user_id, db_service=db_service) 
    
    # Send confirmation email
    try:
        mail_service.send_email_plain_text(
            content=i18n_service.t("auth.email_verified_content", locale),
            subject=i18n_service.t("auth.email_verified_subject", locale),
            recipient=user.email
        )
    except Exception as e:
        logger.error(f"Failed to send confirmation email: {str(e)}")
        pass
    
    return {"msg": i18n_service.t("auth.email_verified_subject", locale), "user": user}


@router.post("/user/resend-verification/{user_id}", status_code=200, tags=["users"])
async def send_new_verification_code(
    user_id: str,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service),
    mail_service: MailService = Depends(get_mail_service),
):
    locale = i18n_service.extract_locale_from_header(request.headers.get("accept-language"))
    
    user = auth_service.get_user(uid=user_id, db_service=db_service)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=i18n_service.t("auth.user_not_found", locale),
        )
    
    return resend_verification_code(
        user, locale, db_service=db_service, 
        mail_service=mail_service, i18n_service=i18n_service
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
        current_user.id, user_update, locale, 
        db_service=db_service, i18n_service=i18n_service
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
        current_user.id, password_update, locale,
        db_service=db_service, i18n_service=i18n_service
    )