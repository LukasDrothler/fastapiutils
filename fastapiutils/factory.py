"""
Factory functions for easy setup
"""
from typing import Optional
from .config import AuthConfig, DatabaseConfig
from .auth_manager import AuthManager
from .i18n import I18n


def create_auth_manager_from_env(
    rsa_keys_path: Optional[str] = None,
    locales_dir: Optional[str] = None,
    default_locale: str = "en"
) -> AuthManager:
    """
    Create an AuthManager instance using environment variables
    
    Args:
        rsa_keys_path: Path to RSA keys directory (uses RSA_KEYS_PATH env var if None)
        locales_dir: Path to locales directory (uses package default if None)
        default_locale: Default locale for i18n
    
    Returns:
        Configured AuthManager instance
    """
    # Create configurations from environment
    auth_config = AuthConfig.from_env(rsa_keys_path)
    auth_config.locales_dir = locales_dir
    auth_config.default_locale = default_locale
    
    db_config = DatabaseConfig.from_env()
    
    # Create AuthManager
    return AuthManager(auth_config, db_config)


def create_auth_manager(
    rsa_keys_path: str,
    db_host: str = "localhost",
    db_port: int = 3306,
    db_user: str = "root",
    db_password: str = "",
    db_database: str = "",
    access_token_expire_minutes: int = 30,
    refresh_token_expire_days: int = 30,
    algorithm: str = "RS256",
    token_url: str = "token",
    locales_dir: Optional[str] = None,
    default_locale: str = "en"
) -> AuthManager:
    """
    Create an AuthManager instance with explicit configuration
    
    Args:
        rsa_keys_path: Path to RSA keys directory
        db_host: Database host
        db_port: Database port
        db_user: Database user
        db_password: Database password
        db_database: Database name
        access_token_expire_minutes: Access token expiration in minutes
        refresh_token_expire_days: Refresh token expiration in days
        algorithm: JWT algorithm
        token_url: Token endpoint URL
        locales_dir: Path to locales directory
        default_locale: Default locale for i18n
    
    Returns:
        Configured AuthManager instance
    """
    # Create configurations
    auth_config = AuthConfig(
        rsa_keys_path=rsa_keys_path,
        access_token_expire_minutes=access_token_expire_minutes,
        refresh_token_expire_days=refresh_token_expire_days,
        algorithm=algorithm,
        token_url=token_url,
        locales_dir=locales_dir,
        default_locale=default_locale
    )
    
    db_config = DatabaseConfig(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_database
    )
    
    # Create AuthManager
    return AuthManager(auth_config, db_config)
