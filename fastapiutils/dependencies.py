"""
Dependency injection container for FastAPI Utils
"""
from typing import Annotated, Optional, Any, Dict, Callable
from functools import lru_cache

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from .models import UserInDB
from .auth_service import AuthService
from .database_service import DatabaseService
from .mail_service import MailService
from .i18n_service import I18nService


class DependencyContainer:
    """Dependency injection container for managing service instances"""
    
    def __init__(self):
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        
    def register_singleton(self, service_name: str, instance: Any) -> None:
        """Register a singleton service instance"""
        self._singletons[service_name] = instance
        
    def register_factory(self, service_name: str, factory: Callable) -> None:
        """Register a factory function for creating service instances"""
        self._factories[service_name] = factory
        
    def get(self, service_name: str) -> Any:
        """Get a service instance"""
        # Check if it's a singleton first
        if service_name in self._singletons:
            return self._singletons[service_name]
            
        # Check if there's a factory for it
        if service_name in self._factories:
            instance = self._factories[service_name]()
            # Cache as singleton after first creation
            self._singletons[service_name] = instance
            return instance
            
        raise ValueError(f"Service '{service_name}' not found in container")
    
    def clear(self) -> None:
        """Clear all registered services"""
        self._factories.clear()
        self._singletons.clear()


# Global dependency container instance
container = DependencyContainer()


def create_database_service() -> DatabaseService:
    """Factory function to create DatabaseService instance"""
    return DatabaseService()


def create_mail_service() -> MailService:
    """Factory function to create MailService instance"""
    return MailService()


def create_i18n_service() -> I18nService:
    """Factory function to create I18nService instance"""
    return I18nService()


def create_auth_service(
    access_token_expire_minutes: int = 30,
    refresh_token_expire_days: int = 30,
    token_url: str = "token",
    private_key_filename: str = "private_key.pem",
    public_key_filename: str = "public_key.pem"
):
    """Factory function to create AuthService instance without dependencies"""
    from .auth_service import AuthService
    return AuthService(
        access_token_expire_minutes=access_token_expire_minutes,
        refresh_token_expire_days=refresh_token_expire_days,
        token_url=token_url,
        private_key_filename=private_key_filename,
        public_key_filename=public_key_filename
    )


def setup_dependencies(
    access_token_expire_minutes: int = 30,
    refresh_token_expire_days: int = 30,
    token_url: str = "token",
    private_key_filename: str = "private_key.pem",
    public_key_filename: str = "public_key.pem"
) -> None:
    """Setup all dependencies in the container"""
    container.clear()
    
    # Register factory functions
    container.register_factory("database_service", create_database_service)
    container.register_factory("mail_service", create_mail_service)
    container.register_factory("i18n_service", create_i18n_service)
    
    # Register auth service factory that depends on other services
    def auth_service_factory():
        return create_auth_service(
            access_token_expire_minutes=access_token_expire_minutes,
            refresh_token_expire_days=refresh_token_expire_days,
            token_url=token_url,
            private_key_filename=private_key_filename,
            public_key_filename=public_key_filename
        )
    
    container.register_factory("auth_service", auth_service_factory)


@lru_cache()
def get_auth_service() -> AuthService:
    """FastAPI dependency function to get AuthService instance"""
    return container.get("auth_service")


@lru_cache()
def get_database_service() -> DatabaseService:
    """FastAPI dependency function to get DatabaseService instance"""
    return container.get("database_service")


@lru_cache()
def get_mail_service() -> MailService:
    """FastAPI dependency function to get MailService instance"""
    return container.get("mail_service")


@lru_cache()
def get_i18n_service() -> I18nService:
    """FastAPI dependency function to get I18nService instance"""
    return container.get("i18n_service")

# Create OAuth2 scheme with correct token URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service = Depends(get_auth_service),
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service)
) -> UserInDB:
    """Dependency to get current user from JWT token"""
    return auth_service.get_current_user(token, db_service=db_service, i18n_service=i18n_service)


def get_current_active_user(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    auth_service = Depends(get_auth_service),
    i18n_service: I18nService = Depends(get_i18n_service)
) -> UserInDB:
    """Dependency to get current active user"""
    return auth_service.get_current_active_user(current_user, i18n_service=i18n_service)


# Convenience type annotations for use in route handlers
CurrentUser = Annotated[UserInDB, Depends(get_current_user)]
CurrentActiveUser = Annotated[UserInDB, Depends(get_current_active_user)]