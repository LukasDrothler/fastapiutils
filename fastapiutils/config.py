from cryptography.hazmat.primitives import serialization
import os

class AuthConfig:
    """Configuration for authentication"""
    
    def __init__(self, 
                 rsa_keys_path: str,
                 access_token_expire_minutes: int = 30,
                 refresh_token_expire_days: int = 30,
                 token_url: str = "token",
                 private_key_filename: str = "private_key.pem",
                 public_key_filename: str = "public_key.pem"):
        
        """Initialize the authentication configuration"""
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

        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self.token_url = token_url