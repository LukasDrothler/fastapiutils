from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class User(BaseModel):
    """Base user model - can be extended in your project"""
    id: str
    username: str
    email: str
    email_verified: bool = False
    premium_level: int = 0
    stripe_customer_id: Optional[str] = None
    disabled: bool = False


class UserInDB(User):
    """User model with database fields - can be extended in your project"""
    hashed_password: str
    created_at: Optional[datetime] = None 
    last_seen: Optional[datetime] = None


class CreateUser(BaseModel):
    """Model for user creation"""
    username: str
    email: str
    password: str


class Token(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data"""
    user_id: str


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh"""
    refresh_token: str


class VerificationCode(BaseModel):
    """Model for email verification codes"""
    user_id: str
    value: str
    created_at: datetime
    verified_at: Optional[datetime] = None


class VerifyEmailRequest(BaseModel):
    """Request model for email verification with code"""
    code: str


class UpdateUser(BaseModel):
    """Model for updating user information"""
    username: Optional[str] = None
    email: Optional[str] = None


class UpdatePassword(BaseModel):
    """Model for updating user password"""
    current_password: str
    new_password: str