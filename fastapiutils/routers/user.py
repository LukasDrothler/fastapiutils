from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapiutils import AuthService, I18nService
from fastapiutils.database_service import DatabaseService
from fastapiutils.mail_service import MailService

from ..models import CreateUser, User
from ..dependencies import get_auth_service, get_database_service, get_mail_service, get_i18n_service, CurrentActiveUser

"""Create user management router with dependency injection"""
router = APIRouter()

@router.post("/users/register", status_code=201, tags=["users"])
async def create_user(
    user: CreateUser,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    db_service: DatabaseService = Depends(get_database_service),
    mail_service: MailService = Depends(get_mail_service),
    i18n_service: I18nService = Depends(get_i18n_service),
):
    locale = i18n_service.extract_locale_from_header(request.headers.get("accept-language"))
    msg = auth_service.create_user(user, locale, db_service=db_service, i18n_service=i18n_service)
    if mail_service is not None:
            try:
                mail_service.send_email_plain_text(
                    content=i18n_service.t("auth.welcome_email_content", locale, username=user.username),
                    subject=i18n_service.t("auth.welcome_email_subject", locale),
                    recipient=user.email
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=i18n_service.t("auth.email_sending_failed", locale, error=str(e))
                )
    return msg

@router.get("/users/me", response_model=User, tags=["users"])
async def read_users_me(
    current_user: CurrentActiveUser,
):
    return current_user