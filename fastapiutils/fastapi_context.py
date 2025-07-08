import jwt
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Annotated
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError

from .mail import MailManager
from .database import DatabaseManager
from .config import AuthConfig, DatabaseConfig, MailConfig
from .models import  UserInDB, CreateUser, TokenData
from .i18n import I18n


class FastapiContext:
    """Main authentication manager class"""
    
    def __init__(self,
                 auth_config: AuthConfig,
                 database_config: DatabaseConfig,
                 mail_config: Optional[MailConfig] = None,
                 custom_locales_dir: Optional[str] = None,
                 default_locale: str = "en",
                 ):
        
        # Store configuration values
        self.access_token_expire_minutes = auth_config.access_token_expire_minutes
        self.refresh_token_expire_days = auth_config.refresh_token_expire_days
        self.token_url = auth_config.token_url
        self.default_locale = default_locale
        self.algorithm = auth_config.algorithm
        self.private_key = auth_config.private_key
        self.public_key = auth_config.public_key
        
        self.db_manager = DatabaseManager(db_config=database_config)

        if mail_config:
            self.mail_manager = MailManager(mail_config)

        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl=self.token_url)
        
        # Initialize i18n (built-in locales are always loaded, custom can override/extend)
        self.i18n = I18n(custom_locales_dir=custom_locales_dir, default_locale=default_locale)

    
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
    
    def get_user(self, username: Optional[str] = None, email: Optional[str] = None) -> Optional[UserInDB]:
        """Get user from database"""
        result = None
        if username and email:
            result = self.db_manager.execute_single_query(
                "SELECT * FROM user WHERE LOWER(username) = LOWER(%s) AND LOWER(email) = LOWER(%s)", 
                (username, email)
            )
        elif email:
            result = self.db_manager.execute_single_query(
                "SELECT * FROM user WHERE LOWER(email) = LOWER(%s)", 
                (email,)
            )
        elif username:
            result = self.db_manager.execute_single_query(
                "SELECT * FROM user WHERE LOWER(username) = LOWER(%s)", 
                (username,)
            )
        
        if result:
            return UserInDB(**result)
        return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        """Authenticate a user"""
        user = self.get_user(username=username)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        
        # Update last_seen
        current_time = datetime.now(timezone.utc)
        self.db_manager.execute_modification_query(
            "UPDATE user SET last_seen = %s WHERE id = %s", 
            (current_time, user.id)
        )
        return user
    
    def validate_new_user(self, user: CreateUser, locale: str = "en"):
        """Validate new user data"""
        if not re.match(r"^\w{3,}$", user.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=self.i18n.t("auth.username_invalid", locale),
            )
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", user.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=self.i18n.t("auth.email_invalid", locale),
            )
        if len(user.password) < 8 or not re.search(r"[A-Z]", user.password) or not re.search(r"[0-9]", user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=self.i18n.t("auth.password_weak", locale),
            )
        
        if self.get_user(username=user.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=self.i18n.t("auth.username_taken", locale),
            )
        if self.get_user(email=user.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=self.i18n.t("auth.email_taken", locale),
            )
    
    def create_user(self, user: CreateUser, locale: str = "en") -> dict:
        """Create a new user"""
        self.validate_new_user(user, locale)
        
        uid = self.db_manager.generate_uuid("user")
        if uid is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=self.i18n.t("auth.user_creation_failed", locale),
            )
        
        hashed_password = self.get_password_hash(user.password)
        
        self.db_manager.execute_modification_query(
            "INSERT INTO user (id, username, email, hashed_password) VALUES (%s, %s, %s, %s)",
            (uid, user.username, user.email, hashed_password)
        )
        
        if self.mail_manager:
            try:
                self.mail_manager.send_email_plain_text(
                    content=self.i18n.t("auth.welcome_email_content", locale, username=user.username),
                    subject=self.i18n.t("auth.welcome_email_subject", locale),
                    recipient=user.email
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=self.i18n.t("auth.email_sending_failed", locale, error=str(e))
                )

        return {"msg": self.i18n.t("auth.user_created", locale)}
    
    def get_current_user(self, token: Annotated[str, Depends]) -> UserInDB:
        """Get current user from token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=self.i18n.t("auth.could_not_validate_credentials"),
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, self.public_key, algorithms=[self.algorithm])
            username = payload.get("sub")
            if username is None:
                raise credentials_exception
            token_data = TokenData(username=username)
        except InvalidTokenError:
            raise credentials_exception
        
        user = self.get_user(username=token_data.username)
        if user is None:
            raise credentials_exception
        return user
    
    def get_current_active_user(self, current_user: Annotated[UserInDB, Depends]) -> UserInDB:
        """Get current active user"""
        if current_user.disabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=self.i18n.t("auth.inactive_user")
            )
        return current_user
    
    def create_dependency_functions(self):
        """Create dependency functions for FastAPI"""
        def get_current_user_dep(token: Annotated[str, Depends(self.oauth2_scheme)]):
            return self.get_current_user(token)
        
        def get_current_active_user_dep(current_user: Annotated[UserInDB, Depends(get_current_user_dep)]):
            return self.get_current_active_user(current_user)
        
        return get_current_user_dep, get_current_active_user_dep
