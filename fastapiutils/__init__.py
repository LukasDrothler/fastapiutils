from .fastapi_context import FastapiContext
from .routers import create_auth_router, create_user_router
from .models import User, UserInDB, CreateUser, Token, TokenData, RefreshTokenRequest
from .database_service import DatabaseService
from .i18n import I18n, extract_locale_from_header
from .config import AuthConfig
from .mail_service import MailService

__version__ = "0.2.0"

__all__ = [
    "DatabaseConfig",
    "AuthConfig",
    "FastapiContext",
    "create_auth_router",
    "create_user_router",
    "User",
    "UserInDB",
    "CreateUser",
    "Token",
    "TokenData",
    "RefreshTokenRequest",
    "DatabaseService",
    "MailService",
    "I18n",
    "extract_locale_from_header",
]
