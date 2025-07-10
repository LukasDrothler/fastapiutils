
from .models import VerificationCode, UserInDB
from .mail_service import MailService
from .database_service import DatabaseService

from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import HTTPException, status

import random


def generate_verification_code() -> str:
    """Generate a 6-digit verification code"""
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])


def get_verification_code_from_db(user_id: str, db_service: DatabaseService = None) -> Optional[VerificationCode]:
    """Get verification code for user from database"""
    result = db_service.execute_single_query(
        "SELECT * FROM verification_code WHERE user_id = %s",
        (user_id,)
    )
    if result:
        return VerificationCode(**result)
    return None


def create_verification_code(user_id: str, db_service: DatabaseService = None) -> str:
    """Create or update verification code for user"""
    new_code = generate_verification_code()
    current_time = datetime.now(timezone.utc)
    
    # Check if verification code already exists for this user
    if get_verification_code_from_db(user_id, db_service=db_service):
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


def can_resend_verification(user_id: str, db_service: DatabaseService = None) -> bool:
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


def verify_user_email_with_code(code: str, user_id: str, locale: str = "en", db_service: DatabaseService = None, i18n_service = None) -> bool:
    """Verify user email using 6-digit code"""
    # Get verification code from database
    verification_record = get_verification_code_from_db(user_id, db_service=db_service)
    
    if not verification_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=i18n_service.t("auth.no_verification_code", locale),
        )
    
    # Check if code matches
    if verification_record.value != code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=i18n_service.t("auth.invalid_verification_code", locale),
        )
    
    # Check if code has already been used
    if verification_record.verified_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=i18n_service.t("auth.verification_code_already_used", locale),
        )
    
    # Check if code is expired (24 hours)
    time_diff = datetime.now(timezone.utc) - verification_record.created_at.replace(tzinfo=timezone.utc)
    if time_diff >= timedelta(hours=24):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=i18n_service.t("auth.verification_code_expired", locale),
        )
    
    # Mark code as verified and update user
    current_time = datetime.now(timezone.utc)
    
    # Update verification code as used
    db_service.execute_modification_query(
        "UPDATE verification_code SET verified_at = %s WHERE user_id = %s",
        (current_time, user_id)
    )
    
    # Update user's email_verified status
    db_service.execute_modification_query(
        "UPDATE user SET email_verified = 1 WHERE id = %s",
        (user_id,)
    )
    
    return True


def resend_verification_code(user: UserInDB, locale: str = "en", db_service: DatabaseService = None, mail_service: MailService = None, i18n_service = None) -> dict:
    """Resend verification code if 1 minute has passed"""
    # Check if user can resend
    if not can_resend_verification(user.id, db_service=db_service):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=i18n_service.t("auth.resend_cooldown", locale),
        )
    
    # Check if email is already verified
    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=i18n_service.t("auth.email_already_verified", locale),
        )
    
    try:
        # Generate new verification code
        verification_code = create_verification_code(user.id, db_service=db_service)
        
        mail_service.send_email_plain_text(
            content=i18n_service.t("auth.email_verification_content", locale, 
                                    username=user.username, 
                                    verification_code=verification_code),
            subject=i18n_service.t("auth.email_verification_subject", locale),
            recipient=user.email
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=i18n_service.t("auth.email_sending_failed", locale, error=str(e))
        )

    return {"msg": i18n_service.t("auth.verification_code_resent", locale)}