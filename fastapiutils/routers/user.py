from fastapi import APIRouter, HTTPException, Request, status

from ..models import CreateUser, User
from ..dependencies import CurrentActiveUser, AuthServiceDependency, DatabaseServiceDependency, MailServiceDependency, I18nServiceDependency

"""Create user management router with dependency injection"""
router = APIRouter()

@router.post("/users/register", status_code=201, tags=["users"])
async def create_user(
    user: CreateUser,
    request: Request,
    auth_service: AuthServiceDependency,
    db_service: DatabaseServiceDependency,
    mail_service: MailServiceDependency,
    i18n_service: I18nServiceDependency,
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