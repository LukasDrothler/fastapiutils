from .fastapi_context import FastapiContext
from .routers import create_auth_router, create_user_router
from .models import User, UserInDB, CreateUser, Token, TokenData, RefreshTokenRequest
from .database import DatabaseManager
from .i18n import I18n, extract_locale_from_header
from .config import AuthConfig, DatabaseConfig, MailConfig
from .mail import MailManager

__version__ = "0.2.0"

__all__ = [
    "DatabaseConfig",
    "AuthConfig",
    "MailConfig",
    "FastapiContext",
    "create_auth_router",
    "create_user_router",
    "User",
    "UserInDB",
    "CreateUser",
    "Token",
    "TokenData",
    "RefreshTokenRequest",
    "DatabaseManager",
    "MailManager",
    "I18n",
    "extract_locale_from_header",
]
