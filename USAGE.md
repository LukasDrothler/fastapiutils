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
app.include_router(create_auth_router(fa_context))
app.include_router(create_user_router(fa_context))
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
from fastapiutils import I18n, FastapiContext

# Built-in translations (en, de) are automatically loaded
# Custom translations can override or extend them
fa_context = FastapiContext(
    rsa_keys_path=os.getenv("RSA_KEYS_PATH", "/path/to/keys"),
    custom_locales_dir="./my_locales",  # Additional/override translations
    default_locale="fr",                # French as default
    # ... other parameters
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
- `rsa_keys_path`: Path to directory containing RSA key files
- `db_host`: Database host 
- `db_port`: Database port
- `db_user`: Database user
- `db_password`: Database password
- `db_name`: Database name

**Optional Parameters (with defaults):**
- `access_token_expire_minutes`: Access token expiration (default: 30)
- `refresh_token_expire_days`: Refresh token expiration (default: 30)
- `token_url`: Token endpoint URL (default: "token")
- `custom_locales_dir`: Custom locales directory for additional/override translations (default: None)
- `default_locale`: Default language (default: "en")
- `private_key_filename`: Name of private key file (default: "private_key.pem")
- `public_key_filename`: Name of public key file (default: "public_key.pem")

## Error Handling

The package raises appropriate HTTP exceptions with localized messages:

- 400 Bad Request - Invalid user data
- 401 Unauthorized - Invalid credentials
- 409 Conflict - Username/email already exists
- 500 Internal Server Error - Database errors
