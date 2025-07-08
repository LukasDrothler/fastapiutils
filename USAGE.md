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
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`)
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
from fastapiutils import FastapiContext, AuthConfig, DatabaseConfig, create_auth_router, create_user_router

app = FastAPI()

# Create configuration objects
auth_config = AuthConfig(
    rsa_keys_path="/path/to/your/keys",
    access_token_expire_minutes=30,
    refresh_token_expire_days=30,
    token_url="token"
)

database_config = DatabaseConfig(
    host="localhost",
    port=3306,
    user="root",
    password="your_password",
    database="your_database"
)

# Create FastAPI context with configuration objects
fa_context = FastapiContext(
    auth_config=auth_config,
    database_config=database_config,
    default_locale="en"
)

# Include routers
app.include_router(create_auth_router(fa_context))
app.include_router(create_user_router(fa_context))
```

### Using Environment Variables

If you want to use environment variables, you can use `os.getenv()` directly in your configuration objects:

```python
import os
from fastapiutils import FastapiContext, AuthConfig, DatabaseConfig

# Create configuration objects using environment variables
auth_config = AuthConfig(
    rsa_keys_path=os.getenv("RSA_KEYS_PATH", "/path/to/keys"),
    access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
    refresh_token_expire_days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30")),
    token_url=os.getenv("TOKEN_URL", "token")
)

database_config = DatabaseConfig(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "3306")),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "")
)

fa_context = FastapiContext(
    auth_config=auth_config,
    database_config=database_config,
    default_locale=os.getenv("DEFAULT_LOCALE", "en")
)
```

### Custom Configuration

```python
from fastapiutils import FastapiContext, AuthConfig, DatabaseConfig

# Create configuration objects with custom settings
auth_config = AuthConfig(
    rsa_keys_path="/etc/ssl/jwt-keys",
    access_token_expire_minutes=60,      # 1 hour tokens
    refresh_token_expire_days=7,         # 1 week refresh
    token_url="auth/token"               # Custom token endpoint
)

database_config = DatabaseConfig(
    host="myserver.com",
    port=3306,
    user="api_user",
    password="secure_password",
    database="production_db"
)

# Create FastAPI context with custom configuration
fa_context = FastapiContext(
    auth_config=auth_config,
    database_config=database_config,
    default_locale="de"                  # German as default
)
```

### Custom RSA Key Filenames

You can specify custom names for your RSA key files:

```python
from fastapiutils import FastapiContext, AuthConfig, DatabaseConfig

# Create auth configuration with custom key filenames
auth_config = AuthConfig(
    rsa_keys_path="/path/to/keys",
    private_key_filename="my_private.pem",    # Custom private key name
    public_key_filename="my_public.pem",      # Custom public key name
    access_token_expire_minutes=30,
    refresh_token_expire_days=30,
    token_url="token"
)

database_config = DatabaseConfig(
    host="localhost",
    port=3306,
    user="root",
    password="your_password",
    database="your_database"
)

# Create FastAPI context
fa_context = FastapiContext(
    auth_config=auth_config,
    database_config=database_config,
    default_locale="en"
)
```

## API Endpoints

### Authentication Endpoints

- `POST /token` - Login with username/password
- `POST /token/refresh` - Refresh access token

### User Endpoints

- `POST /users/register` - Register new user
- `GET /users/me` - Get current user info

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

The package includes built-in English and German translations that are always loaded. You can add custom translations or override existing ones by providing a custom locales directory:

```python
import os
from fastapiutils import I18n, FastapiContext, AuthConfig, DatabaseConfig

# Create configuration objects
auth_config = AuthConfig(rsa_keys_path=os.getenv("RSA_KEYS_PATH", "/path/to/keys"))
database_config = DatabaseConfig(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "3306")),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "")
)

# Built-in translations (en, de) are automatically loaded
# Custom translations can override or extend them
fa_context = FastapiContext(
    auth_config=auth_config,
    database_config=database_config,
    custom_locales_dir="./my_locales",  # Additional/override translations
    default_locale="fr"                # French as default
)
```

### How Translation Override Works

1. **Built-in locales** (en.json, de.json) are always loaded first
2. **Custom locales** from `custom_locales_dir` are loaded second and can:
   - Override existing keys in built-in locales
   - Add new keys to existing locales  
   - Add completely new locales

**Example custom locale file** (`./my_locales/en.json`):
```json
{
  "auth": {
    "incorrect_credentials": "Wrong username or password!",
    "custom_message": "This is a custom message"
  },
  "app": {
    "welcome": "Welcome to our app!"
  }
}
```

This will override the built-in "incorrect_credentials" message and add new translations.

## Configuration Reference

### FastapiContext Parameters

**Required Parameters:**
- `auth_config`: AuthConfig object containing authentication settings
- `database_config`: DatabaseConfig object containing database connection settings

**Optional Parameters (with defaults):**
- `custom_locales_dir`: Custom locales directory for additional/override translations (default: None)
- `default_locale`: Default language (default: "en")

### AuthConfig Parameters

**Required Parameters:**
- `rsa_keys_path`: Path to directory containing RSA key files

**Optional Parameters (with defaults):**
- `access_token_expire_minutes`: Access token expiration (default: 30)
- `refresh_token_expire_days`: Refresh token expiration (default: 30)
- `token_url`: Token endpoint URL (default: "token")
- `private_key_filename`: Name of private key file (default: "private_key.pem")
- `public_key_filename`: Name of public key file (default: "public_key.pem")

### DatabaseConfig Parameters

**Required Parameters:**
- `host`: Database host 
- `port`: Database port
- `user`: Database user
- `password`: Database password
- `database`: Database name

## Error Handling

The package raises appropriate HTTP exceptions with localized messages:

- 400 Bad Request - Invalid user data
- 401 Unauthorized - Invalid credentials
- 409 Conflict - Username/email already exists
- 500 Internal Server Error - Database errors
