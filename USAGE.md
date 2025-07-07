# FastAPI Utils Usage Guide

## Installation

```bash
pip install git+https://github.com/LukasDrothler/fastapiutils
```

## Prerequisites

### Database Setup

You need a MySQL database with the following user table structure:

```sql
CREATE TABLE `user` (
  `id` varchar(36) NOT NULL,
  `username` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `email_verified` tinyint(1) NOT NULL DEFAULT '0',
  `premium_level` int DEFAULT '0',
  `stripe_customer_id` varchar(50) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_seen` timestamp NULL DEFAULT NULL,
  `disabled` tinyint(1) NOT NULL DEFAULT '0',
  `hashed_password` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

### RSA Keys

Generate RSA key pair for JWT signing:

```bash
# Generate private key
openssl genpkey -algorithm RSA -out private_key.pem -pkcs8

# Generate public key
openssl rsa -pubout -in private_key.pem -out public_key.pem
```

## Basic Usage

### Simple Setup

```python
from fastapi import FastAPI
from fastapiutils import FastapiContext, create_auth_router, create_user_router

app = FastAPI()

# Create auth manager with direct parameters
fa_context = FastapiContext(
    rsa_keys_path="/path/to/your/keys",
    db_host="localhost",
    db_port=3306,
    db_user="root",
    db_password="your_password",
    db_name="your_database",
    access_token_expire_minutes=30,
    refresh_token_expire_days=30,
    default_locale="en"
)

# Include routers
app.include_router(create_auth_router(fa_context), prefix="/auth")
app.include_router(create_user_router(fa_context), prefix="/api")
```

### Using Environment Variables

If you want to use environment variables, you can use `os.getenv()` directly in your parameters:

```python
import os
from fastapiutils import FastapiContext

# Create configuration using environment variables
fa_context = FastapiContext(
    rsa_keys_path=os.getenv("RSA_KEYS_PATH", "/path/to/keys"),
    db_host=os.getenv("DB_HOST", "localhost"),
    db_port=int(os.getenv("DB_PORT", "3306")),
    db_user=os.getenv("DB_USER", "root"),
    db_password=os.getenv("DB_PASSWORD", ""),
    db_name=os.getenv("DB_NAME", ""),
    access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
    refresh_token_expire_days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30")),
    token_url=os.getenv("TOKEN_URL", "token"),
    default_locale=os.getenv("DEFAULT_LOCALE", "en")
)
```

### Custom Configuration

```python
from fastapiutils import FastapiContext

# Create auth manager with custom parameters
fa_context = FastapiContext(
    rsa_keys_path="/etc/ssl/jwt-keys",
    db_host="myserver.com",
    db_port=3306,
    db_user="api_user",
    db_password="secure_password",
    db_name="production_db",
    access_token_expire_minutes=60,      # 1 hour tokens
    refresh_token_expire_days=7,         # 1 week refresh
    token_url="auth/token",              # Custom token endpoint
    default_locale="de"                  # German as default
)
```

### Custom RSA Key Filenames

You can specify custom names for your RSA key files:

```python
from fastapiutils import FastapiContext

# Create auth manager with custom key filenames
fa_context = FastapiContext(
    rsa_keys_path="/path/to/keys",
    private_key_filename="my_private.pem",    # Custom private key name
    public_key_filename="my_public.pem",      # Custom public key name
    db_host="localhost",
    # ... other parameters
)
```

### Environment Helper Functions

For convenience, you can also use the helper functions to get configuration from environment variables:

```python
from fastapiutils import get_db_config_from_env, get_auth_config_from_env

# Get configurations as dictionaries
db_config = get_db_config_from_env()
auth_config = get_auth_config_from_env()

# Use them to create FastapiContext
fa_context = FastapiContext(
    rsa_keys_path=auth_config["rsa_keys_path"],
    **db_config,  # Unpack database config
    **{k: v for k, v in auth_config.items() if k != "rsa_keys_path"}  # Unpack auth config except rsa_keys_path
)
```

## API Endpoints

### Authentication Endpoints

- `POST /auth/token` - Login with username/password
- `POST /auth/token/refresh` - Refresh access token

### User Endpoints

- `POST /api/users/register` - Register new user
- `GET /api/users/me` - Get current user info

## Extending Models

You can extend the base models in your project:

```python
from fastapiutils import User as BaseUser, UserInDB as BaseUserInDB
from pydantic import BaseModel
from typing import Optional

class User(BaseUser):
    """Extended user model with custom fields"""
    phone_number: Optional[str] = None
    company: Optional[str] = None

class UserInDB(BaseUserInDB):
    """Extended user DB model"""
    phone_number: Optional[str] = None
    company: Optional[str] = None
```

## Custom Authentication Dependencies

```python
from fastapi import Depends
from fastapiutils import FastapiContext

# Get dependency functions
get_current_user, get_current_active_user = fa_context.create_dependency_functions()

@app.get("/protected")
async def protected_route(current_user = Depends(get_current_active_user)):
    return {"user": current_user.username}
```

## Internationalization

The package supports i18n with English and German built-in. You can add custom translations:

```python
import os
from fastapiutils import I18n, FastapiContext

# Create auth manager with custom locale directory
fa_context = FastapiContext(
    rsa_keys_path=os.getenv("RSA_KEYS_PATH", "/path/to/keys"),
    locales_dir="./my_locales",  # Custom locale directory
    default_locale="fr",         # French as default
    # ... other parameters
)

# Or create I18n instance directly
i18n = I18n(locales_dir="./my_locales", default_locale="fr")
fa_context = FastapiContext(
    rsa_keys_path=os.getenv("RSA_KEYS_PATH", "/path/to/keys"),
    i18n=i18n,
    # ... other parameters
)
```

## Configuration Reference

### FastapiContext Parameters

- `rsa_keys_path`: Path to directory containing RSA key files
- `private_key_filename`: Name of private key file (default: "private_key.pem")
- `public_key_filename`: Name of public key file (default: "public_key.pem")
- `db_host`: Database host (default: "localhost")
- `db_port`: Database port (default: 3306)
- `db_user`: Database user (default: "root")
- `db_password`: Database password (default: "")
- `db_name`: Database name (default: "")
- `access_token_expire_minutes`: Access token expiration (default: 30)
- `refresh_token_expire_days`: Refresh token expiration (default: 30)
- `token_url`: Token endpoint URL (default: "token")
- `locales_dir`: Custom locales directory (optional)
- `default_locale`: Default language (default: "en")
- `i18n`: Custom I18n instance (optional)

## Error Handling

The package raises appropriate HTTP exceptions with localized messages:

- 400 Bad Request - Invalid user data
- 401 Unauthorized - Invalid credentials
- 409 Conflict - Username/email already exists
- 500 Internal Server Error - Database errors
