from .config import AuthConfig, DatabaseConfig
from .auth_manager import AuthManager
from .routers import create_auth_router, create_user_router
from .models import User, UserInDB, CreateUser, Token, TokenData, RefreshTokenRequest
from .database import DatabaseManager
from .i18n import I18n, extract_locale_from_header
from .factory import create_auth_manager_from_env, create_auth_manager

__version__ = "0.1.0"

__all__ = [
    "AuthConfig",
    "DatabaseConfig", 
    "AuthManager",
    "create_auth_router",
    "create_user_router",
    "User",
    "UserInDB",
    "CreateUser",
    "Token",
    "TokenData",
    "RefreshTokenRequest",
    "DatabaseManager",
    "I18n",
    "extract_locale_from_header",
    "create_auth_manager_from_env",
    "create_auth_manager",
]
