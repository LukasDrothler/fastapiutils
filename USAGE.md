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
from fastapiutils import AuthConfig, DatabaseConfig, AuthManager, create_auth_router, create_user_router

app = FastAPI()

# Configure database connection
db_config = DatabaseConfig(
    host="localhost",
    port=3306,
    user="root",
    password="your_password",
    database="your_database"
)

# Configure authentication settings
auth_config = AuthConfig(
    rsa_keys_path="/path/to/your/keys",
    access_token_expire_minutes=30,
    refresh_token_expire_days=30,
    algorithm="RS256",
    default_locale="en"
)

# Create auth manager
auth_manager = AuthManager(auth_config, db_config)

# Include routers
app.include_router(create_auth_router(auth_manager), prefix="/auth")
app.include_router(create_user_router(auth_manager), prefix="/api")
```

### Using Environment Variables

You can also use environment variables with the `from_env()` class methods:

```python
# Set environment variables:
# DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
# RSA_KEYS_PATH

from fastapiutils import AuthConfig, DatabaseConfig, AuthManager

# Create configurations from environment
db_config = DatabaseConfig.from_env()
auth_config = AuthConfig.from_env()

# Create auth manager
auth_manager = AuthManager(auth_config, db_config)
```

### Custom Configuration

```python
from fastapiutils import AuthConfig, DatabaseConfig, AuthManager

# Custom database configuration
db_config = DatabaseConfig(
    host="myserver.com",
    port=3306,
    user="api_user",
    password="secure_password",
    database="production_db"
)

# Custom authentication configuration
auth_config = AuthConfig(
    rsa_keys_path="/etc/ssl/jwt-keys",
    access_token_expire_minutes=60,      # 1 hour tokens
    refresh_token_expire_days=7,         # 1 week refresh
    algorithm="RS256",
    token_url="auth/token",              # Custom token endpoint
    default_locale="de"                  # German as default
)

auth_manager = AuthManager(auth_config, db_config)
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
from fastapiutils import AuthManager

# Get dependency functions
get_current_user, get_current_active_user = auth_manager.create_dependency_functions()

@app.get("/protected")
async def protected_route(current_user = Depends(get_current_active_user)):
    return {"user": current_user.username}
```

## Internationalization

The package supports i18n with English and German built-in. You can add custom translations:

```python
from fastapiutils import I18n, AuthConfig

# Custom translations directory
auth_config = AuthConfig(
    rsa_keys_path="/path/to/keys",
    locales_dir="./my_locales",  # Custom locale directory
    default_locale="fr"          # French as default
)

# Or create I18n instance directly
i18n = I18n(locales_dir="./my_locales", default_locale="fr")
auth_manager = AuthManager(auth_config, db_config, i18n=i18n)
```

## Configuration Reference

### AuthConfig

- `rsa_keys_path`: Path to directory containing `private_key.pem` and `public_key.pem`
- `access_token_expire_minutes`: Access token expiration (default: 30)
- `refresh_token_expire_days`: Refresh token expiration (default: 30)
- `algorithm`: JWT algorithm (default: "RS256")
- `token_url`: Token endpoint URL (default: "token")
- `locales_dir`: Custom locales directory (optional)
- `default_locale`: Default language (default: "en")

### DatabaseConfig

- `host`: Database host (default: "localhost")
- `port`: Database port (default: 3306)
- `user`: Database user (default: "root")
- `password`: Database password
- `database`: Database name

## Error Handling

The package raises appropriate HTTP exceptions with localized messages:

- 400 Bad Request - Invalid user data
- 401 Unauthorized - Invalid credentials
- 409 Conflict - Username/email already exists
- 500 Internal Server Error - Database errors
