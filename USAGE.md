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

### Environment Variables

Create a `.env` file or set environment variables:

**Required Environment Variables:**
```bash
# Database configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=your_database

# RSA Keys path
RSA_KEYS_PATH=./keys
```

**Optional Environment Variables (for email functionality):**
```bash
# Email configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

## Basic Usage

### Simple Setup

```python
from fastapi import FastAPI
from fastapiutils import setup_dependencies
from fastapiutils.routers import auth, user
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Setup dependency injection container
setup_dependencies(
    default_locale="en",            # Default language
    access_token_expire_minutes=30, # Token expiration
    refresh_token_expire_days=30,   # Refresh token expiration
    token_url="token"               # Token endpoint URL
)

# Include built-in routers
app.include_router(auth.router)
app.include_router(user.router)
```

### Advanced Configuration

```python
from fastapiutils import setup_dependencies

# Advanced configuration with custom settings
setup_dependencies(
    custom_locales_dir="./my_locales",    # Custom translation files
    default_locale="de",                  # German as default
    access_token_expire_minutes=60,       # 1 hour access tokens
    refresh_token_expire_days=7,          # 1 week refresh tokens
    token_url="auth/token",               # Custom token endpoint
    private_key_filename="my_private.pem", # Custom key filenames
    public_key_filename="my_public.pem"
)
```

### Custom RSA Key Filenames

You can specify custom names for your RSA key files:

```python
from fastapiutils import setup_dependencies

# Setup with custom key filenames
setup_dependencies(
    private_key_filename="custom_private.pem",
    public_key_filename="custom_public.pem",
    # ... other parameters ...
)
```

## API Endpoints

### Authentication Endpoints

- `POST /token` - Login with username/password
- `POST /token/refresh` - Refresh access token

### User Endpoints

- `POST /users/register` - Register new user (sends welcome email if SMTP is configured)
- `GET /users/me` - Get current user info

**Note**: When SMTP environment variables are configured, the `/users/register` endpoint will automatically send a localized welcome email to new users.

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

## Using Dependencies in Custom Routes

```python
from fastapi import Depends, APIRouter
from fastapiutils import CurrentActiveUser
from fastapiutils.dependencies import get_database_service

router = APIRouter()

@router.get("/protected")
async def protected_route(
    current_user: CurrentActiveUser,
    db_service: DatabaseService = Depends(get_database_service)
):
    return {"user": current_user.username, "user_id": current_user.id}
```

## Internationalization

The package includes built-in English and German translations that are always loaded. You can add custom translations or override existing ones by providing a custom locales directory:

```python
from fastapiutils import setup_dependencies

# Built-in translations (en, de) are automatically loaded
# Custom translations can override or extend them
setup_dependencies(
    custom_locales_dir="./my_locales",  # Additional/override translations
    default_locale="fr",                # French as default
    # ... other parameters ...
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

### setup_dependencies() Parameters

**All Parameters (with defaults):**
- `custom_locales_dir`: Custom locales directory for additional/override translations (default: None)
- `default_locale`: Default language (default: "en")
- `access_token_expire_minutes`: Access token expiration (default: 30)
- `refresh_token_expire_days`: Refresh token expiration (default: 30)
- `token_url`: Token endpoint URL (default: "token")
- `private_key_filename`: Name of private key file (default: "private_key.pem")
- `public_key_filename`: Name of public key file (default: "public_key.pem")

### Environment Variables

**Required Environment Variables:**
- `DB_HOST`: Database host 
- `DB_PORT`: Database port
- `DB_USER`: Database user
- `DB_PASSWORD`: Database password
- `DB_NAME`: Database name
- `RSA_KEYS_PATH`: Path to directory containing RSA key files

**Optional Environment Variables (for email functionality):**
- `SMTP_SERVER`: SMTP server address
- `SMTP_PORT`: SMTP server port
- `SMTP_USER`: SMTP username/email
- `SMTP_PASSWORD`: SMTP password/app password

**Note**: When SMTP environment variables are provided, users will receive welcome emails upon registration with localized content.

## Error Handling

The package raises appropriate HTTP exceptions with localized messages:

- 400 Bad Request - Invalid user data
- 401 Unauthorized - Invalid credentials
- 409 Conflict - Username/email already exists
- 500 Internal Server Error - Database errors

## Production Deployment

For production deployment, consider the following:

### Environment Configuration

```bash
# Production .env file
DB_HOST=your-production-db-host
DB_PORT=3306
DB_USER=your-production-user
DB_PASSWORD=your-secure-password
DB_NAME=your-production-db

RSA_KEYS_PATH=/etc/ssl/jwt-keys

# Optional: Email configuration
SMTP_SERVER=smtp.your-domain.com
SMTP_PORT=587
SMTP_USER=noreply@your-domain.com
SMTP_PASSWORD=your-secure-smtp-password
```

### Production App Structure

```python
# main.py
from fastapi import FastAPI
from fastapiutils import setup_dependencies
from fastapiutils.routers import auth, user
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Create FastAPI app with production settings
app = FastAPI(
    title="Your Production API",
    description="Your API description",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") == "development" else None,  # Disable docs in production
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") == "development" else None
)

# Setup dependencies with production settings
setup_dependencies(
    default_locale="en",
    access_token_expire_minutes=15,  # Shorter tokens for production
    refresh_token_expire_days=7,     # Shorter refresh for production
    token_url="auth/token"
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(user.router, prefix="/users", tags=["users"])

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### Security Considerations

1. **Use HTTPS in production** - Never send JWT tokens over HTTP
2. **Secure your RSA keys** - Store them securely and with proper file permissions
3. **Use strong database passwords** - Consider using connection pooling
4. **Configure CORS properly** - Only allow necessary origins
5. **Monitor your logs** - The package logs important security events
6. **Regular key rotation** - Consider implementing RSA key rotation
