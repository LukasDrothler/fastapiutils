from dataclasses import dataclass
from typing import Optional
import os


@dataclass
class DatabaseConfig:
    """Configuration for database connection"""
    host: str = "localhost"
    port: int = 3306
    user: str = "root"
    password: str = ""
    database: str = ""
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create configuration from environment variables"""
        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", ""),
        )


@dataclass
class AuthConfig:
    """Configuration for authentication settings"""
    rsa_keys_path: str
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    algorithm: str = "RS256"
    token_url: str = "token"
    locales_dir: Optional[str] = None
    default_locale: str = "en"
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if not os.path.exists(self.rsa_keys_path):
            raise ValueError(f"RSA keys path does not exist: {self.rsa_keys_path}")
        
        private_key_path = os.path.join(self.rsa_keys_path, "private_key.pem")
        public_key_path = os.path.join(self.rsa_keys_path, "public_key.pem")
        
        if not os.path.exists(private_key_path):
            raise ValueError(f"Private key not found: {private_key_path}")
        if not os.path.exists(public_key_path):
            raise ValueError(f"Public key not found: {public_key_path}")
    
    @classmethod
    def from_env(cls, rsa_keys_path: Optional[str] = None) -> "AuthConfig":
        """Create configuration from environment variables"""
        if rsa_keys_path is None:
            rsa_keys_path = os.getenv("RSA_KEYS_PATH")
            if rsa_keys_path is None:
                raise ValueError("RSA_KEYS_PATH environment variable must be set or rsa_keys_path must be provided")
        
        return cls(
            rsa_keys_path=rsa_keys_path,
            access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
            refresh_token_expire_days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30")),
            algorithm=os.getenv("AUTH_ALGORITHM", "RS256"),
            token_url=os.getenv("TOKEN_URL", "token"),
            default_locale=os.getenv("DEFAULT_LOCALE", "en"),
        )
