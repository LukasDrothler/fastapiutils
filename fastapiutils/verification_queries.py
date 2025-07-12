"""
Verification database queries
"""
from .models import VerificationCode
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
    def get_verification_code_by_user_id(user_id: str, db_service: DatabaseService = None) -> Optional[VerificationCode]:
        """Get regular verification code for user from database"""
        result = db_service.execute_single_query(
            "SELECT * FROM verification_code WHERE user_id = %s",
            (user_id,)
        )
        if result:
            return VerificationCode(**result)
        return None


    @staticmethod
    def create_verification_code(user_id: str, db_service: DatabaseService = None) -> str:
        """Create or update regular verification code for user"""
        new_code = VerificationQueries._generate_verification_code()
        current_time = datetime.now(timezone.utc)
        
        # Check if verification code already exists for this user
        existing_code = VerificationQueries.get_verification_code_by_user_id(user_id, db_service=db_service)
        
        if existing_code:
            # Update existing code
            db_service.execute_modification_query(
                "UPDATE verification_code SET value = %s, created_at = %s, verified_at = NULL WHERE user_id = %s",
                (new_code, current_time, user_id)
            )
        else:
            # Insert new code
            db_service.execute_modification_query(
                "INSERT INTO verification_code (user_id, value, created_at) VALUES (%s, %s, %s)",
                (user_id, new_code, current_time)
            )
        
        return new_code
    

    @staticmethod
    def mark_verification_code_as_used(user_id: str, db_service: DatabaseService = None) -> None:
        """Mark regular verification code as used"""
        current_time = datetime.now(timezone.utc)
        db_service.execute_modification_query(
            "UPDATE verification_code SET verified_at = %s WHERE user_id = %s",
            (current_time, user_id)
        )
    

    @staticmethod
    def can_send_verification(user_id: str, db_service: DatabaseService = None) -> bool:
        """Check if user can resend verification code (1 minute cooldown)"""
        existing_code = db_service.execute_single_query(
            "SELECT created_at FROM verification_code WHERE user_id = %s",
            (user_id,)
        )
        
        if not existing_code:
            return True  # No existing code, can send
        
        created_at = existing_code['created_at']
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        
        # Check if 1 minute has passed since last code generation
        time_diff = datetime.now(timezone.utc) - created_at.replace(tzinfo=timezone.utc)
        return time_diff >= timedelta(minutes=1)
    
    @staticmethod
    def update_user_email_verified_status(user_id: str, verified: bool = True, db_service: DatabaseService = None) -> None:
        """Update user's email_verified status"""
        db_service.execute_modification_query(
            "UPDATE user SET email_verified = %s WHERE id = %s",
            (1 if verified else 0, user_id)
        )
    
    @staticmethod
    def update_user_email(user_id: str, new_email: str, db_service: DatabaseService = None) -> None:
        """Update user's email and mark as verified"""
        db_service.execute_modification_query(
            "UPDATE user SET email = %s WHERE id = %s",
            (new_email, user_id)
        )
