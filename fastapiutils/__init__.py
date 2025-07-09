from .auth_service import AuthService
from .models import User, UserInDB, CreateUser, Token, TokenData, RefreshTokenRequest
from .database_service import DatabaseService
from .i18n_service import I18nService, extract_locale_from_header
from .mail_service import MailService
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
    "DatabaseService",
    "MailService",
    "I18nService",
    "extract_locale_from_header",
    "setup_dependencies",
    "get_auth_service",
    "get_database_service",
    "get_mail_service",
    "get_i18n_service",
    "CurrentUser",
    "CurrentActiveUser",
]
