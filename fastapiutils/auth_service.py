from .database_service import DatabaseService
from .mail_service import MailService
from .i18n_service import I18nService
import jwt
import re
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from cryptography.hazmat.primitives import serialization

from .models import UserInDB, CreateUser


class AuthService:
    """Service for handling authentication-related operations"""
    
    def __init__(self,
                 access_token_expire_minutes=30,
                 refresh_token_expire_days=30,
                 token_url="token",
                 private_key_filename: str = "private_key.pem",
                 public_key_filename: str = "public_key.pem",
                 ):
        
        """Initialize the authentication configuration"""
        rsa_keys_path=os.getenv("RSA_KEYS_PATH")
        if not os.path.exists(rsa_keys_path):
            raise ValueError(f"RSA keys path does not exist: {rsa_keys_path}")
        
        self.algorithm = "RS256"
        private_key_path = os.path.join(rsa_keys_path, private_key_filename)
        public_key_path = os.path.join(rsa_keys_path, public_key_filename)
        
        if not os.path.exists(private_key_path):
            raise ValueError(f"Private key not found: {private_key_path}")
        if not os.path.exists(public_key_path):
            raise ValueError(f"Public key not found: {public_key_path}")
        
        with open(private_key_path, 'rb') as f:
            self.private_key = serialization.load_pem_private_key(f.read(), password=None)
        with open(public_key_path, 'rb') as f:
            self.public_key = serialization.load_pem_public_key(f.read())
        
        # Store configuration values
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self.token_url = token_url

        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl=self.token_url)

    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return self.pwd_context.hash(password)
    
    def create_bearer_token(self, username: str, is_refresh: bool = False) -> str:
        """Create a JWT token"""
        data = {"sub": username}
        to_encode = data.copy()
        if is_refresh:
            expires_delta = timedelta(days=self.refresh_token_expire_days)
        else:
            expires_delta = timedelta(minutes=self.access_token_expire_minutes)
        
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.private_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def get_user(self, username: Optional[str] = None, email: Optional[str] = None, db_service: DatabaseService=None) -> Optional[UserInDB]:
        """Get user from database"""
        result = None
        if username and email:
            result = db_service.execute_single_query(
                "SELECT * FROM user WHERE LOWER(username) = LOWER(%s) AND LOWER(email) = LOWER(%s)", 
                (username, email)
            )
        elif email:
            result = db_service.execute_single_query(
                "SELECT * FROM user WHERE LOWER(email) = LOWER(%s)", 
                (email,)
            )
        elif username:
            result = db_service.execute_single_query(
                "SELECT * FROM user WHERE LOWER(username) = LOWER(%s)", 
                (username,)
            )
        
        if result:
            return UserInDB(**result)
        return None
    
    def authenticate_user(self, username: str, password: str, db_service: DatabaseService = None) -> Optional[UserInDB]:
        """Authenticate a user"""
        user = self.get_user(username=username, db_service=db_service)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        
        # Update last_seen
        current_time = datetime.now(timezone.utc)
        db_service.execute_modification_query(
            "UPDATE user SET last_seen = %s WHERE id = %s", 
            (current_time, user.id)
        )
        return user
    
    def validate_new_user(self, user: CreateUser, locale: str = "en", db_service: DatabaseService = None, i18n_service: I18nService = None):
        """Validate new user data"""
        if not re.match(r"^\w{3,}$", user.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=i18n_service.t("auth.username_invalid", locale),
            )
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", user.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=i18n_service.t("auth.email_invalid", locale),
            )
        if len(user.password) < 8 or not re.search(r"[A-Z]", user.password) or not re.search(r"[0-9]", user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=i18n_service.t("auth.password_weak", locale),
            )
        
        if self.get_user(username=user.username, db_service=db_service):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=i18n_service.t("auth.username_taken", locale),
            )
        if self.get_user(email=user.email, db_service=db_service):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=i18n_service.t("auth.email_taken", locale),
            )
    
    def create_user(self, user: CreateUser, locale: str = "en", db_service: DatabaseService = None, mail_service: Optional[MailService] = None, i18n_service: I18nService = None) -> dict:
        """Create a new user"""
        self.validate_new_user(user, locale, db_service=db_service, i18n_service=i18n_service)
        
        uid = db_service.generate_uuid("user")
        if uid is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=i18n_service.t("auth.user_creation_failed", locale),
            )
        
        hashed_password = self.get_password_hash(user.password)
        
        db_service.execute_modification_query(
            "INSERT INTO user (id, username, email, hashed_password) VALUES (%s, %s, %s, %s)",
            (uid, user.username, user.email, hashed_password)
        )
        
        if mail_service is not None:
            try:
                mail_service.send_email_plain_text(
                    content=i18n_service.t("auth.welcome_email_content", locale, username=user.username),
                    subject=i18n_service.t("auth.welcome_email_subject", locale),
                    recipient=user.email
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=i18n_service.t("auth.email_sending_failed", locale, error=str(e))
                )

        return {"msg": i18n_service.t("auth.user_created", locale)}
    
    def get_current_user(self, token: str, db_service: DatabaseService = None, i18n_service: I18nService = None) -> UserInDB:
        """Get current user from JWT token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=i18n_service.t("auth.could_not_validate_credentials", "en"),
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, self.public_key, algorithms=[self.algorithm])
            username = payload.get("sub")
            if username is None:
                raise credentials_exception
        except jwt.InvalidTokenError:
            raise credentials_exception
            
        user = self.get_user(username=username, db_service=db_service)
        if user is None:
            raise credentials_exception
        return user
    
    def get_current_active_user(self, current_user: UserInDB, i18n_service: I18nService = None) -> UserInDB:
        """Get current active user (not disabled)"""
        if current_user.disabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=i18n_service.t("auth.inactive_user", "en")
            )
        return current_user