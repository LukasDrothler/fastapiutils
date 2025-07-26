from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class User(BaseModel):
    """Base user model - can be extended in your project"""
    id: str
    username: str
    email: str
    email_verified: bool = False
    is_admin: bool = False
    premium_level: int = 0
    stripe_customer_id: Optional[str] = None
    disabled: bool = False


class UserInDBNoPassword(User):
    """User model for admin views - can be extended in your project"""
    created_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None


class UserInDB(UserInDBNoPassword):
    """User model with database fields - can be extended in your project"""
    hashed_password: str


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
    email: str


class SendVerificationRequest(BaseModel):
    """Request model for sending verification code"""
    email: str


class UpdateUser(BaseModel):
    """Model for updating user information"""
    username: Optional[str] = None


class UpdatePassword(BaseModel):
    """Model for updating user password"""
    current_password: str
    new_password: str


class UpdateForgottenPassword(BaseModel):
    """Model for updating forgotten password"""
    email: str
    new_password: str
    verification_code: str


class CreateCancellation(BaseModel):
    email: str
    name: str
    last_name: str
    address: str
    town: str
    town_number: str
    is_unordinary: int=0
    reason: Optional[str]=None
    last_invoice_number: str
    termination_date: datetime

class Cancellation(CreateCancellation):
    id: int
    is_archived: int=0
    created_at: datetime


class CreateFeedback(BaseModel):
    email: Optional[str] = None
    text: str

class Feedback(CreateFeedback):
    id: int
    is_archived: int=0
    created_at: datetime