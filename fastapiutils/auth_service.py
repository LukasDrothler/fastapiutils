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
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

import jwt
import os
import logging

logger = logging.getLogger('uvicorn.error')

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
        if "RSA_KEYS_DIR" in os.environ:
            _rsa_keys_path = os.environ["RSA_KEYS_DIR"]
            logger.info(f"Using  '{_rsa_keys_path}' from environment variable 'RSA_KEYS_DIR'")
        else:
            _rsa_keys_path = os.path.join(os.path.dirname(__file__), "keys")
            logger.info(f"Using default RSA keys directory since 'RSA_KEYS_DIR' not set")
        
        ## create dir if not exists
        if not os.path.exists(_rsa_keys_path):
            os.makedirs(_rsa_keys_path)
            logger.info(f"Created RSA keys directory at '{_rsa_keys_path}'")
        
        self.algorithm = "RS256"
        private_key_path = os.path.join(_rsa_keys_path, private_key_filename)
        public_key_path = os.path.join(_rsa_keys_path, public_key_filename)
        
        if not os.path.exists(private_key_path) or not os.path.exists(public_key_path):
            logger.info(f"No RSA keys found at {_rsa_keys_path}, with filenames {private_key_filename} and {public_key_filename}. Generating new keys..")
            
            key = rsa.generate_private_key(
                backend=default_backend(),
                public_exponent=65537,
                key_size=2048
            )
            private_key = key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption()
            )
            public_key = key.public_key().public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo
            )
            with open(private_key_path, 'wb') as f:
                f.write(private_key)
            with open(public_key_path, 'wb') as f:
                f.write(public_key)

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


    def create_bearer_token(self, user: UserInDB, is_refresh: bool = False) -> str:
        """Create a JWT token"""
        data = {
            "sub": user.id,
            "username": user.username,
            "email": user.email,
            "email_verified": user.email_verified,
            "premium_level": user.premium_level,
            "is_admin": user.is_admin,
            "stripe_customer_id": user.stripe_customer_id,
            "disabled": user.disabled,
            "last_seen": user.last_seen.isoformat() if user.last_seen else None,
            "created_at": user.created_at.isoformat() if user.created_at else None
            }
        to_encode = data.copy()
        if is_refresh:
            expires_delta = timedelta(days=self.refresh_token_expire_days)
        else:
            expires_delta = timedelta(minutes=self.access_token_expire_minutes)
        
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.private_key, algorithm=self.algorithm)
        return encoded_jwt


    def authenticate_user(self, username: str, password: str, db_service: DatabaseService) -> Optional[UserInDB]:
        """Authenticate a user"""
        user = UserQueries.get_user_by_username(username, db_service=db_service)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        
        # Update last_seen
        UserQueries.update_user_last_seen(user.id, db_service=db_service)
        return user


    def register_new_user(
            self, 
            user: CreateUser,
            db_service: DatabaseService,
            mail_service: MailService,
            i18n_service: I18nService,
            locale: str
            ) -> dict:
        """Create a new user"""
        UserValidators.validate_new_user(user, locale, db_service=db_service, i18n_service=i18n_service)
        hashed_password = self.get_password_hash(user.password)
        
        UserQueries.create_user(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password,
            db_service=db_service,
            i18n_service=i18n_service,
            locale=locale
        )
        
        # Generate 6-digit verification code
        verification_code = VerificationQueries.create_verification_code(
            user=None,
            email=user.email,
            db_service=db_service,
            i18n_service=i18n_service,
            locale=locale
        )
        
        mail_service.send_email_verification_mail(
            recipient=user.email,
            username=user.username,
            verification_code=verification_code,
            i18n_service=i18n_service,
            locale=locale
        )  

        return {"detail": i18n_service.t("api.auth.user_management.user_created_verify_email", locale)}


    def get_current_user(self, token: str, db_service: DatabaseService, i18n_service: I18nService) -> UserInDB:
        """Get current user from JWT token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=i18n_service.t("api.auth.credentials.could_not_validate_credentials", "en"),
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, self.public_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            if user_id is None:
                raise credentials_exception
        except jwt.InvalidTokenError:
            raise credentials_exception
            
        user = UserQueries.get_user_by_id(user_id, db_service=db_service)
        if user is None:
            raise credentials_exception
        return user


    def get_current_active_user(self, current_user: UserInDB, i18n_service: I18nService) -> UserInDB:
        """Get current active user (not disabled)"""
        if current_user.disabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=i18n_service.t("api.auth.credentials.inactive_user", "en")
            )
        return current_user


    def get_current_admin_user(self, current_user: UserInDB, i18n_service: I18nService) -> UserInDB:
        """Get current admin user"""
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=i18n_service.t("api.auth.credentials.admin_required", "en")
            )
        return current_user


    def update_user(
            self,
            user_id: str,
            user_update: UpdateUser,
            db_service: DatabaseService,
            i18n_service: I18nService,
            locale: str
            ) -> dict:
        """Update user information"""
        # Get current user to verify they exist
        current_user = UserQueries.get_user_by_id(user_id, db_service=db_service)
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=i18n_service.t("api.auth.user_management.user_not_found", locale)
            )

        UserValidators.validate_user_update(user_update, locale, db_service, i18n_service)
        fields_updated = UserQueries.update_user_fields(user_id, user_update, db_service=db_service)
        
        if not fields_updated:
            return {"detail": i18n_service.t("api.auth.user_management.no_changes_made", locale)}
        
        try:
            return {"detail": i18n_service.t("api.auth.user_management.user_updated_successfully", locale)}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=i18n_service.t("api.auth.user_management.user_update_failed", locale, error=str(e))
            )


    def update_password(
            self,
            user_id: str,
            db_service: DatabaseService,
            i18n_service: I18nService,
            locale: str,
            password_update: Optional[UpdatePassword] = None,
            new_password: Optional[str] = None
            ) -> dict:
        """Update user password"""
        # Get current user to verify they exist and get their current password
        current_user = UserQueries.get_user_by_id(user_id, db_service=db_service)
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=i18n_service.t("api.auth.user_management.user_not_found", locale)
            )
        
        UserValidators.validate_new_password(
                password_update=password_update,
                current_hashed_password=current_user.hashed_password,
                new_password=new_password,
                pwd_context=self.pwd_context,
                locale=locale,
                i18n_service=i18n_service
            )

        if password_update is not None:
            new_hashed_password = self.get_password_hash(password_update.new_password)
        elif new_password is not None:
            new_hashed_password = self.get_password_hash(new_password)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=i18n_service.t("api.auth.password_management.no_password_provided", locale)
            )
        
        # Update password in database
        try:
            UserQueries.update_user_password(
                user_id=user_id, 
                hashed_password=new_hashed_password, 
                db_service=db_service)
            return {"detail": i18n_service.t("api.auth.password_management.password_updated_successfully", locale)}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=i18n_service.t("api.auth.password_management.password_update_failed", locale, error=str(e))
            )