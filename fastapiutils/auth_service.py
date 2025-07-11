from .verification_queries import VerificationQueries
from .models import UserInDB, CreateUser, UpdateUser, UpdatePassword
from .database_service import DatabaseService
from .mail_service import MailService
from .i18n_service import I18nService
from .user_validators import UserValidators
from .user_queries import UserQueries

from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from cryptography.hazmat.primitives import serialization

import jwt
import os



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


    def create_bearer_token(self, user_id: str, is_refresh: bool = False) -> str:
        """Create a JWT token"""
        data = {"sub": user_id}
        to_encode = data.copy()
        if is_refresh:
            expires_delta = timedelta(days=self.refresh_token_expire_days)
        else:
            expires_delta = timedelta(minutes=self.access_token_expire_minutes)
        
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.private_key, algorithm=self.algorithm)
        return encoded_jwt

    
    def get_user(self, uid: Optional[str] = None, username: Optional[str] = None, email: Optional[str] = None, db_service: DatabaseService=None) -> Optional[UserInDB]:
        """Get user from database"""
        if uid:
            return UserQueries.get_user_by_id(uid, db_service=db_service)
        elif username and email:
            return UserQueries.get_user_by_username_and_email(username, email, db_service=db_service)
        elif email:
            return UserQueries.get_user_by_email(email, db_service=db_service)
        elif username:
            return UserQueries.get_user_by_username(username, db_service=db_service)
        return None


    def authenticate_user(self, username: str, password: str, db_service: DatabaseService = None) -> Optional[UserInDB]:
        """Authenticate a user"""
        user = self.get_user(username=username, db_service=db_service)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        
        # Update last_seen
        UserQueries.update_user_last_seen(user.id, db_service=db_service)
        return user


    def create_user(self, user: CreateUser, locale: str = "en", db_service: DatabaseService = None, mail_service: MailService = None, i18n_service: I18nService = None) -> dict:
        """Create a new user"""
        UserValidators.validate_new_user(user, locale, db_service=db_service, i18n_service=i18n_service)
        
        uid = UserQueries.generate_user_uuid(db_service=db_service)
        if uid is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=i18n_service.t("auth.user_creation_failed", locale),
            )
        
        hashed_password = self.get_password_hash(user.password)
        
        UserQueries.create_user(uid, user.username, user.email, hashed_password, db_service=db_service)
        
        # Generate 6-digit verification code
        verification_code = VerificationQueries.create_verification_code(uid, db_service=db_service)
        
        try:
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

        return {"msg": i18n_service.t("auth.user_created_verify_email", locale)}


    def get_current_user(self, token: str, db_service: DatabaseService = None, i18n_service: I18nService = None) -> UserInDB:
        """Get current user from JWT token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=i18n_service.t("auth.could_not_validate_credentials", "en"),
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, self.public_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            if user_id is None:
                raise credentials_exception
        except jwt.InvalidTokenError:
            raise credentials_exception
            
        user = self.get_user(uid=user_id, db_service=db_service)
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


    def update_user(self, user_id: str, user_update: UpdateUser, locale: str = "en", db_service: DatabaseService = None, i18n_service: I18nService = None) -> dict:
        """Update user information"""
        # Get current user to verify they exist
        current_user = self.get_user(uid=user_id, db_service=db_service)
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=i18n_service.t("auth.user_not_found", locale)
            )
        
        # Validate update data
        UserValidators.validate_user_update(user_update, user_id, locale, db_service, i18n_service)
        
        # Update user fields
        fields_updated = UserQueries.update_user_fields(user_id, user_update, db_service=db_service)
        
        if not fields_updated:
            return {"msg": i18n_service.t("auth.no_changes_made", locale)}
        
        try:
            return {"msg": i18n_service.t("auth.user_updated_successfully", locale)}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=i18n_service.t("auth.user_update_failed", locale, error=str(e))
            )


    def update_password(self, user_id: str, password_update: UpdatePassword, locale: str = "en", db_service: DatabaseService = None, i18n_service: I18nService = None) -> dict:
        """Update user password"""
        # Get current user to verify they exist and get their current password
        current_user = self.get_user(uid=user_id, db_service=db_service)
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=i18n_service.t("auth.user_not_found", locale)
            )
        
        # Validate password update
        UserValidators.validate_password_update(password_update, current_user.hashed_password, 
                                               self.pwd_context, locale, i18n_service)
        
        # Hash new password
        new_hashed_password = self.get_password_hash(password_update.new_password)
        
        # Update password in database
        try:
            UserQueries.update_user_password(user_id, new_hashed_password, db_service=db_service)
            return {"msg": i18n_service.t("auth.password_updated_successfully", locale)}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=i18n_service.t("auth.password_update_failed", locale, error=str(e))
            )