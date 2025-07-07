from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class User(BaseModel):
    id: str
    username: str
    email: str
    email_verified: bool = False
    premium_level: int = 0
    stripe_customer_id: Optional[str] = None
    disabled: bool = False

class UserInDB(User):
    hashed_password: str
    created_at: Optional[datetime] = None 
    last_seen: Optional[datetime] = None

class CreateUser(BaseModel):
    username: str
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class CreatePet(BaseModel):
    name: str
    species: Optional[str] = None