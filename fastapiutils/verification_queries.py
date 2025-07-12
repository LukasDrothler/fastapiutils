"""
Verification database queries
"""
from fastapi import HTTPException, status

from .user_queries import UserQueries
from .i18n_service import I18nService
from .models import UserInDB, VerificationCode
from .database_service import DatabaseService

from datetime import datetime, timezone, timedelta
from typing import Optional
import random


class VerificationQueries:
    """Collection of database queries for verification operations"""
    
    @staticmethod
    def _generate_verification_code() -> str:
        """Generate a 6-digit verification code"""
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])


    @staticmethod
    def get_verification_code_by_user_id(user_id: str, db_service: DatabaseService) -> Optional[VerificationCode]:
        """Get regular verification code for user from database"""
        result = db_service.execute_single_query(
            "SELECT * FROM verification_code WHERE user_id = %s",
            (user_id,)
        )
        if result:
            return VerificationCode(**result)
        return None


    @staticmethod
    def create_verification_code(
        user: Optional[UserInDB],
        email: str,
        db_service: DatabaseService,
        i18n_service: I18nService,
        locale: str = "en"
        ) -> str:
        """Create or update regular verification code for user"""
        if not user: user = UserQueries.get_user_by_email(email=email, db_service=db_service)
        VerificationQueries.check_can_send_verification(
            user=user,
            locale=locale,
            db_service=db_service,
            i18n_service=i18n_service
        )

        new_code = VerificationQueries._generate_verification_code()
        current_time = datetime.now(timezone.utc)

        # Check if verification code already exists for this user
        existing_code = VerificationQueries.get_verification_code_by_user_id(
            user_id=user.id, db_service=db_service
        )
        if existing_code:
            # Update existing code
            db_service.execute_modification_query(
                "UPDATE verification_code SET value = %s, created_at = %s, verified_at = NULL WHERE user_id = %s",
                (new_code, current_time, user.id)
            )
        else:
            # Insert new code
            db_service.execute_modification_query(
                "INSERT INTO verification_code (user_id, value, created_at) VALUES (%s, %s, %s)",
                (user.id, new_code, current_time)
            )
        return new_code
    

    @staticmethod
    def mark_verification_code_as_used(user_id: str, db_service: DatabaseService) -> None:
        """Mark regular verification code as used"""
        current_time = datetime.now(timezone.utc)
        db_service.execute_modification_query(
            "UPDATE verification_code SET verified_at = %s WHERE user_id = %s",
            (current_time, user_id)
        )
    

    @staticmethod
    def check_can_send_verification(
        user: Optional[UserInDB],
        db_service: DatabaseService,
        i18n_service: I18nService,
        locale: str = "en"
        ) -> bool:
        """Check if user can resend verification code (1 minute cooldown)"""
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=i18n_service.t("auth.user_not_found", locale),
            )
        
        existing_code = db_service.execute_single_query(
            "SELECT created_at FROM verification_code WHERE user_id = %s",
            (user.id,)
        )

        if not existing_code:
            return None  # No existing code, can send
        
        created_at = existing_code['created_at']
        
        
        # Check if 1 minute has passed since last code generation
        time_diff = datetime.now(timezone.utc) - created_at.replace(tzinfo=timezone.utc)
        if time_diff <= timedelta(minutes=1):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=i18n_service.t("auth.resend_cooldown", locale),
            )
        return None
    
    @staticmethod
    def update_user_email_verified_status(user_id: str, db_service: DatabaseService, verified: bool = True) -> None:
        """Update user's email_verified status"""
        db_service.execute_modification_query(
            "UPDATE user SET email_verified = %s WHERE id = %s",
            (1 if verified else 0, user_id)
        )
    
    @staticmethod
    def update_user_email(user_id: str, new_email: str, db_service: DatabaseService) -> None:
        """Update user's email and mark as verified"""
        db_service.execute_modification_query(
            "UPDATE user SET email = %s WHERE id = %s",
            (new_email, user_id)
        )
