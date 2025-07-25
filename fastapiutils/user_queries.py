"""
Authentication database queries
"""
from fastapi import HTTPException, status
from .i18n_service import I18nService
from .models import UserInDBNoPassword, UserInDB, UpdateUser
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
    def get_user_by_stripe_customer_id(
        stripe_customer_id: str, 
        db_service: DatabaseService
        ) -> Optional[UserInDB]:
        """Get user by Stripe customer ID"""
        result = db_service.execute_single_query(
            "SELECT * FROM user WHERE stripe_customer_id = %s", 
            (stripe_customer_id,)
        )
        if result:
            return UserInDB(**result)
        return None


    @staticmethod
    def get_username_by_id(
        user_id: str,
        db_service: DatabaseService,
        i18n_service: I18nService,
        locale: str = "en"
        ) -> str:
        """Get username by user ID"""
        user = UserQueries.get_user_by_id(user_id, db_service)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=i18n_service.t("api.auth.user_management.user_not_found", locale),
            )
        return user.username
    
    
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
                detail=i18n_service.t("api.auth.user_management.user_creation_failed", locale),
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
    
    @staticmethod
    def get_user_ids_to_names(
        user_ids: list[str],
        db_service: DatabaseService,
        i18n_service: I18nService,
        locale: str = "en"
        ) -> dict[str, str]:
        """Get user names by their IDs"""
        if not user_ids:
            return {}
        
        placeholders = ', '.join(['%s'] * len(user_ids))
        try:
            results = db_service.execute_query(
                sql = f"SELECT id, username FROM user WHERE id IN ({placeholders})",
                params=tuple(user_ids)
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=i18n_service.t(
                    "api.auth.user_management.user_ids_to_names_failed",
                    locale=locale,
                    error=str(e)
                    ),
            )

        return {result['id']: result['username'] for result in results} if results else {}


    @staticmethod
    def get_all_users(
        db_service: DatabaseService,
        i18n_service: I18nService,
        locale: str = "en"
        ) -> list[UserInDBNoPassword]:
        """Get all users from the database"""
        try:
            results = db_service.execute_query("SELECT * FROM user")
            return [UserInDBNoPassword(**result) for result in results] if results else []
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=i18n_service.t(
                    "api.auth.user_management.get_all_users_failed",
                    locale=locale,
                    error=str(e)
                ),
            )
        
    @staticmethod
    def delete_user(
        user_id: str,
        db_service: DatabaseService,
        i18n_service: I18nService,
        locale: str = "en"
        ) -> dict:
        """Delete a user by ID"""
        # First check if user exists
        existing_user = UserQueries.get_user_by_id(user_id, db_service)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=i18n_service.t("api.auth.user_management.user_not_found", locale),
            )
        
        try:
            db_service.execute_modification_query(
                sql="DELETE FROM user WHERE id = %s",
                params=(user_id,)
            )
            return {"detail": i18n_service.t("api.auth.user_management.user_deleted_successfully", locale=locale)}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=i18n_service.t(
                    "api.auth.user_management.user_deletion_failed",
                    locale=locale,
                    error=str(e)
                ),
            )


    @staticmethod
    def update_user_premium_level(
        user_id: str,
        new_premium_level: int,
        db_service: DatabaseService,
        i18n_service: I18nService,
        locale: str = "en",
        stripe_customer_id: Optional[str] = None
        ) -> dict:
        """Update user's premium level"""
        try:
            if stripe_customer_id is not None:
                db_service.execute_modification_query(
                    sql="UPDATE user SET premium_level = %s, stripe_customer_id = %s WHERE id = %s",
                    params=(new_premium_level, stripe_customer_id, user_id)
                )
            else:
                db_service.execute_modification_query(
                    sql="UPDATE user SET premium_level = %s WHERE id = %s",
                    params=(new_premium_level, user_id)
                )
            return {"detail": i18n_service.t(
                key="api.auth.user_management.premium_level_updated", 
                locale=locale,
                user_id=user_id, 
                new_premium_level=new_premium_level
            )}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=i18n_service.t(
                    key="api.auth.user_management.premium_level_update_failed",
                    locale=locale,
                    user_id=user_id,
                    error=str(e)
                ),
            )