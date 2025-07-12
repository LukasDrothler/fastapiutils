"""
Authentication database queries
"""
from fastapi import HTTPException, status
from .i18n_service import I18nService
from .models import UserInDB, UpdateUser
from .database_service import DatabaseService

from datetime import datetime, timezone
from typing import Optional


class UserQueries:
    """Collection of database queries for authentication operations"""
    
    @staticmethod
    def get_user_by_id(user_id: str, db_service: DatabaseService) -> Optional[UserInDB]:
        """Get user by ID"""
        result = db_service.execute_single_query(
            "SELECT * FROM user WHERE id = %s", 
            (user_id,)
        )
        if result:
            return UserInDB(**result)
        return None
    
    @staticmethod
    def get_user_by_username(username: str, db_service: DatabaseService) -> Optional[UserInDB]:
        """Get user by username"""
        result = db_service.execute_single_query(
            "SELECT * FROM user WHERE LOWER(username) = LOWER(%s)", 
            (username,)
        )
        if result:
            return UserInDB(**result)
        return None
    
    @staticmethod
    def get_user_by_email(email: str, db_service: DatabaseService) -> Optional[UserInDB]:
        """Get user by email"""
        result = db_service.execute_single_query(
            "SELECT * FROM user WHERE LOWER(email) = LOWER(%s)", 
            (email,)
        )
        if result:
            return UserInDB(**result)
        return None
    
    @staticmethod
    def get_user_by_username_and_email(username: str, email: str, db_service: DatabaseService) -> Optional[UserInDB]:
        """Get user by username and email"""
        result = db_service.execute_single_query(
            "SELECT * FROM user WHERE LOWER(username) = LOWER(%s) AND LOWER(email) = LOWER(%s)", 
            (username, email)
        )
        if result:
            return UserInDB(**result)
        return None
    
    @staticmethod
    def create_user(username: str,
                    email: str,
                    hashed_password: str,
                    db_service: DatabaseService,
                    i18n_service: I18nService,
                    locale: str
                   ) -> None:
        """Create a new user in the database"""
        uid = UserQueries.generate_user_uuid(db_service=db_service)
        if uid is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=i18n_service.t("auth.user_creation_failed", locale),
            )
        db_service.execute_modification_query(
            "INSERT INTO user (id, username, email, hashed_password) VALUES (%s, %s, %s, %s)",
            (uid, username, email, hashed_password)
        )
    
    @staticmethod
    def update_user_last_seen(user_id: str, db_service: DatabaseService) -> None:
        """Update user's last seen timestamp"""
        current_time = datetime.now(timezone.utc)
        db_service.execute_modification_query(
            "UPDATE user SET last_seen = %s WHERE id = %s", 
            (current_time, user_id)
        )
    
    @staticmethod
    def update_user_password(
        user_id: str,
        hashed_password: str,
        db_service: DatabaseService
        ) -> None:
        """Update user's password"""
        db_service.execute_modification_query(
            "UPDATE user SET hashed_password = %s WHERE id = %s",
            (hashed_password, user_id)
        )
    
    @staticmethod
    def update_user_fields(user_id: str, user_update: UpdateUser, db_service: DatabaseService) -> bool:
        """Update user fields dynamically"""
        update_fields = []
        update_values = []
        
        if user_update.username is not None:
            update_fields.append("username = %s")
            update_values.append(user_update.username)
        
        if update_fields:
            update_values.append(user_id)
            query = f"UPDATE user SET {', '.join(update_fields)} WHERE id = %s"
            db_service.execute_modification_query(query, tuple(update_values))
        
        return len(update_fields) > 0  # Return True if any fields were updated

    @staticmethod
    def generate_user_uuid(db_service: DatabaseService) -> Optional[str]:
        """Generate a new UUID for a user"""
        return db_service.generate_uuid("user")