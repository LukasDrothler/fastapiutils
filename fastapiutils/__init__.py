from .auth_service import AuthService
from .models import User, UserInDB, CreateUser, Token, TokenData, RefreshTokenRequest, VerificationCode, VerifyEmailRequest
from .database_service import DatabaseService
from .mail_service import MailService
from .i18n_service import I18nService
from .dependencies import (
    setup_dependencies, 
    get_auth_service, 
    get_database_service, 
    get_mail_service, 
    get_i18n_service,
    CurrentUser, 
    CurrentActiveUser
)

__version__ = "0.3.0"

__all__ = [
    "AuthService",
    "User",
    "UserInDB",
    "CreateUser",
    "Token",
    "TokenData",
    "RefreshTokenRequest",
    "VerificationCode",
    "VerifyEmailRequest",
    "DatabaseService",
    "MailService",
    "I18nService",
    "setup_dependencies",
    "get_auth_service",
    "get_database_service",
    "get_mail_service",
    "get_i18n_service",
    "CurrentUser",
    "CurrentActiveUser",
]
