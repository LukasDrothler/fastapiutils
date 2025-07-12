"""
Authentication validation utilities
"""
from .models import CreateUser, UpdateUser, UpdatePassword
from .database_service import DatabaseService
from .i18n_service import I18nService
from .user_queries import UserQueries

from fastapi import HTTPException, status
import re


class UserValidators:
    """Collection of validation methods for authentication operations"""
    
    @staticmethod
    def validate_username_format(username: str, locale: str, i18n_service: I18nService) -> None:
        """Validate username format"""
        if not re.match(r"^\w{3,}$", username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=i18n_service.t("auth.username_invalid", locale),
            )
    
    @staticmethod
    def validate_email_format(email: str, locale: str, i18n_service: I18nService) -> None:
        """Validate email format"""
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=i18n_service.t("auth.email_invalid", locale),
            )
    
    @staticmethod
    def validate_password_strength(password: str, locale: str, i18n_service: I18nService) -> None:
        """Validate password strength"""
        if (len(password) < 8 or 
            not re.search(r"[A-Z]", password) or 
            not re.search(r"[0-9]", password)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=i18n_service.t("auth.password_weak", locale),
            )
    
    @staticmethod
    def validate_username_unique(
        username: str, locale: str,
        db_service: DatabaseService, i18n_service: I18nService
        ) -> None:
        """Validate that username is unique (excluding current user if updating)"""
        existing_user = UserQueries.get_user_by_username(username, db_service=db_service)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=i18n_service.t("auth.username_taken", locale),
            )
    
    @staticmethod
    def validate_email_unique(
        email: str,
        locale: str, 
        db_service: DatabaseService, 
        i18n_service: I18nService
        ) -> None:
        """Validate that email is unique (excluding current user if updating)"""
        
        existing_user = UserQueries.get_user_by_email(email, db_service=db_service)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=i18n_service.t("auth.email_taken", locale),
            )
    
    @staticmethod
    def validate_new_user(user: CreateUser, locale: str, db_service: DatabaseService, 
                         i18n_service: I18nService) -> None:
        """Validate all fields for new user creation"""
        UserValidators.validate_username_format(user.username, locale, i18n_service)
        UserValidators.validate_email_format(user.email, locale, i18n_service)
        UserValidators.validate_password_strength(user.password, locale, i18n_service)
        UserValidators.validate_username_unique(
            username=user.username,
            locale=locale, 
            db_service=db_service, 
            i18n_service=i18n_service)
        UserValidators.validate_email_unique(
            email=user.email,
            locale=locale, 
            db_service=db_service, 
            i18n_service=i18n_service
        )
    
    @staticmethod
    def validate_user_update(user_update: UpdateUser, locale: str, 
                           db_service: DatabaseService, i18n_service: I18nService) -> None:
        """Validate fields for user update"""
        if user_update.username is not None:
            UserValidators.validate_username_format(user_update.username, locale, i18n_service)
            UserValidators.validate_username_unique(user_update.username, locale, db_service, i18n_service)
    
    @staticmethod
    def validate_password_update(password_update: UpdatePassword, current_hashed_password: str, 
                               pwd_context, locale: str, i18n_service: I18nService) -> None:
        """Validate password update"""
        # Verify current password
        if not pwd_context.verify(password_update.current_password, current_hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=i18n_service.t("auth.current_password_incorrect", locale)
            )
        
        # Validate new password strength
        UserValidators.validate_password_strength(password_update.new_password, locale, i18n_service)
        
        # Check if new password is the same as current password
        if pwd_context.verify(password_update.new_password, current_hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=i18n_service.t("auth.new_password_same_as_current", locale)
            )
