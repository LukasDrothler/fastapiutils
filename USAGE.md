# FastAPI Utils Usage Guide

## Installation

```bash
pip install git+https://github.com/LukasDrothler/fastapiutils
```

## Prerequisites

### Database Setup

You need a MySQL database with the following table structure. **Important**: The database schema is now **automatically initialized** when the `DatabaseService` starts up. The library will execute the `requirements.sql` file to create all necessary tables.

You only need to create an empty MySQL database - all tables will be created automatically when the application starts.

**Tables created automatically:**

```sql
CREATE TABLE `user` (
  `id` varchar(36) NOT NULL,
  `username` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `email_verified` tinyint(1) NOT NULL DEFAULT '0',
  `premium_level` int DEFAULT '0',
  `is_admin` tinyint(1) NOT NULL DEFAULT '0',
  `stripe_customer_id` varchar(50) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_seen` timestamp NULL DEFAULT NULL,
  `disabled` tinyint(1) NOT NULL DEFAULT '0',
  `hashed_password` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `verification_code` (
  `user_id` varchar(36) NOT NULL,
  `value` varchar(6) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `verified_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`user_id`),
  FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Customer form tables
CREATE TABLE `cancellation` (
  `id` int NOT NULL AUTO_INCREMENT,
  `email` varchar(255) NOT NULL,
  `name` varchar(100) NOT NULL,
  `last_name` varchar(100) NOT NULL,
  `address` varchar(255) NOT NULL,
  `town` varchar(100) NOT NULL,
  `town_number` varchar(10) NOT NULL,
  `is_unordinary` tinyint DEFAULT '0',
  `reason` varchar(255) DEFAULT NULL,
  `last_invoice_number` varchar(50) NOT NULL,
  `termination_date` date NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `is_archived` tinyint DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `feedback` (
  `id` int NOT NULL AUTO_INCREMENT,
  `email` varchar(255) DEFAULT NULL,
  `text` varchar(500) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `is_archived` tinyint DEFAULT '0',
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
RSA_KEYS_DIR=./keys

# Email configuration (REQUIRED for email verification)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Optional customization
DEFAULT_LOCALE=en
LOCALES_DIR=./custom_locales
COLOR_CONFIG_FILE=./config/colors.json
```

## Basic Usage

### Simple Setup

```python
from fastapi import FastAPI
from fastapiutils import setup_dependencies
from fastapiutils.routers import auth, user, customer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Setup dependency injection container
setup_dependencies(
    access_token_expire_minutes=30, # Token expiration
    refresh_token_expire_days=30,   # Refresh token expiration
    token_url="token"               # Token endpoint URL
)

# Include built-in routers
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(customer.router)  # Customer forms management
```

### Advanced Configuration

```python
from fastapiutils import setup_dependencies

# Advanced configuration with custom settings
setup_dependencies(
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

## API Workflows

### User Registration and Email Verification

```python
import requests

# 1. Register new user
response = requests.post("http://localhost:8000/user/register", json={
    "username": "johndoe",
    "email": "john@example.com", 
    "password": "SecurePass123"
})
# Returns: {"msg": "User created successfully. Please check your email for a 6-digit verification code."}

# 2. Verify email with 6-digit code (received via email)
response = requests.post("http://localhost:8000/user/verify-email", json={
    "email": "john@example.com",
    "code": "123456"
})
# Returns: {"msg": "Email verified successfully!"}

# 3. User can now login and access protected endpoints
response = requests.post("http://localhost:8000/token", data={
    "username": "johndoe",
    "password": "SecurePass123"
})
# Returns: {"access_token": "...", "token_type": "bearer", "refresh_token": "..."}
```

### Password Reset Workflow

```python
import requests

# 1. Request password reset (no authentication required)
response = requests.post("http://localhost:8000/user/forgot-password/request", json={
    "email": "john@example.com"
})
# Returns: {"msg": "Password reset verification code has been sent to your email address"}

# 2. Verify reset code (user receives 6-digit code via email)
response = requests.post("http://localhost:8000/user/forgot-password/verify", json={
    "email": "john@example.com",
    "code": "654321"
})
# Returns: {"msg": "Verification code verified successfully"}

# 3. Change password using verified code
response = requests.post("http://localhost:8000/user/forgot-password/change", json={
    "email": "john@example.com",
    "verification_code": "654321",
    "new_password": "NewSecurePass456"
})
# Returns: {"msg": "Password updated successfully"}
```

### Email Change Workflow

```python
import requests

# User must be authenticated for email change
headers = {"Authorization": "Bearer your_access_token"}

# 1. Request email change (sends verification code to NEW email)
response = requests.post("http://localhost:8000/user/me/email/change",
    headers=headers,
    json={"email": "newemail@example.com"}
)
# Returns: {"msg": "Verification code sent to your new email address. Please check your email."}

# 2. Verify new email with 6-digit code (sent to new email address)
response = requests.post("http://localhost:8000/user/me/email/verify",
    headers=headers,
    json={
        "email": "newemail@example.com",
        "code": "789012"
    }
)
# Returns: {"msg": "Email address updated successfully"}
```

### Password Change (Authenticated)

```python
import requests

# User must be authenticated
headers = {"Authorization": "Bearer your_access_token"}

# Change password (requires current password)
response = requests.put("http://localhost:8000/user/me/password",
    headers=headers,
    json={
        "current_password": "OldPassword123",
        "new_password": "NewPassword456"
    }
)
# Returns: {"msg": "Password updated successfully"}
```

## API Endpoints

### Authentication Endpoints

- `POST /token` - Login with username/password
- `POST /token/refresh` - Refresh access token

### User Endpoints

#### User Management
- `POST /user/register` - Register new user (requires email verification)
- `GET /user/me` - Get current user info (requires verified email)
- `PUT /user/me` - Update current user information
- `PUT /user/me/password` - Change current user's password

#### Email Verification
- `POST /user/verify-email` - Verify email with 6-digit code
- `POST /user/resend-verification` - Resend verification code (1-minute cooldown)

#### Email Change
- `POST /user/me/email/change` - Request email change (sends verification code to new email)
- `POST /user/me/email/verify` - Verify new email with 6-digit code

#### Password Reset
- `POST /user/forgot-password/request` - Request password reset (sends verification code to email)
- `POST /user/forgot-password/verify` - Verify password reset code  
- `POST /user/forgot-password/change` - Change password using verified reset code

**Note**: Email verification is mandatory. Users must verify their email with a 6-digit code sent via email before they can access protected endpoints.

### Customer Form Endpoints

Customer forms allow you to collect cancellation requests and feedback from users. These endpoints have two access levels:

#### Public Endpoints (no authentication required)
- `POST /customer/cancellation` - Submit cancellation request
- `POST /customer/feedback` - Submit feedback

#### Admin-Only Endpoints (require CurrentAdminUser)
- `GET /customer/cancellations` - Get all cancellation requests (admin only)
- `GET /customer/feedback` - Get all feedback submissions (admin only)
- `PATCH /customer/cancellation/{id}/archive` - Archive cancellation request (admin only)
- `PATCH /customer/feedback/{id}/archive` - Archive feedback submission (admin only)

## Customer Forms Management

### Setting Up Admin Access

To use admin endpoints, you need to create an admin user. First, register a regular user:

```python
import requests

# Register admin user
response = requests.post("http://localhost:8000/user/register", json={
    "username": "admin",
    "email": "admin@yourcompany.com",
    "password": "SecureAdminPass123"
})

# Verify email (check email for 6-digit code)
response = requests.post("http://localhost:8000/user/verify-email", json={
    "email": "admin@yourcompany.com",
    "code": "123456"
})
```

Then manually update the database to make them an admin:

```sql
-- Make user an admin
UPDATE user SET is_admin = 1 WHERE email = 'admin@yourcompany.com';
```

### Public Customer Forms

Anyone can submit cancellation requests or feedback without authentication:

```python
import requests

# Submit cancellation request
response = requests.post("http://localhost:8000/customer/cancellation", json={
    "email": "customer@example.com",
    "name": "John",
    "last_name": "Doe", 
    "address": "123 Main St",
    "town": "Springfield",
    "town_number": "12345",
    "is_unordinary": False,
    "reason": None,  # Optional, only for unordinary cancellations
    "last_invoice_number": "INV-2024-001",
    "termination_date": "2024-12-31"
})
# Returns: {"id": 1, "msg": "Cancellation request submitted successfully"}

# Submit feedback
response = requests.post("http://localhost:8000/customer/feedback", json={
    "email": "customer@example.com",  # Optional
    "text": "Great service, very satisfied!"
})
# Returns: {"id": 1, "msg": "Feedback submitted successfully"}
```

### Admin Customer Forms Management

Admin users can view and manage all submissions:

```python
import requests

# Get admin token
response = requests.post("http://localhost:8000/token", data={
    "username": "admin",
    "password": "SecureAdminPass123"
})
admin_token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {admin_token}"}

# Get all cancellation requests
response = requests.get("http://localhost:8000/customer/cancellations", headers=headers)
cancellations = response.json()
# Returns: [{"id": 1, "email": "customer@example.com", "name": "John", ...}, ...]

# Get all feedback submissions
response = requests.get("http://localhost:8000/customer/feedback", headers=headers)
feedback_list = response.json()
# Returns: [{"id": 1, "email": "customer@example.com", "text": "Great service!", ...}, ...]

# Archive a cancellation request (hide from main list)
response = requests.patch("http://localhost:8000/customer/cancellation/1/archive", headers=headers)
# Returns: {"msg": "Cancellation archived successfully"}

# Archive feedback
response = requests.patch("http://localhost:8000/customer/feedback/1/archive", headers=headers)
# Returns: {"msg": "Feedback archived successfully"}
```

### Customer Form Models

The package provides Pydantic models for customer forms:

#### Cancellation Models
- `CreateCancellation` - Request model for submitting cancellation
  - `email: str` - Customer email
  - `name: str` - Customer first name
  - `last_name: str` - Customer last name
  - `address: str` - Customer address
  - `town: str` - Customer town
  - `town_number: str` - Town/postal code
  - `is_unordinary: bool` - Whether cancellation is unordinary
  - `reason: Optional[str]` - Reason (required if is_unordinary is True)
  - `last_invoice_number: str` - Last invoice number
  - `termination_date: date` - Desired termination date

- `Cancellation` - Response model with additional fields
  - All CreateCancellation fields plus:
  - `id: int` - Unique cancellation ID
  - `created_at: datetime` - Submission timestamp
  - `is_archived: bool` - Archive status

#### Feedback Models
- `CreateFeedback` - Request model for submitting feedback
  - `email: Optional[str]` - Customer email (optional)
  - `text: Optional[str]` - Feedback text (optional)

- `Feedback` - Response model with additional fields
  - All CreateFeedback fields plus:
  - `id: int` - Unique feedback ID
  - `created_at: datetime` - Submission timestamp
  - `is_archived: bool` - Archive status

### Using Customer Forms in Your App

Include the customer router in your FastAPI application:

```python
from fastapi import FastAPI
from fastapiutils.routers import auth, user, customer

app = FastAPI()

# Include routers
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(customer.router)  # Add customer forms
```

The customer forms are automatically integrated with your database and follow the same patterns as the user management system.

## Request/Response Models

The package provides several Pydantic models for API requests and responses:

### Authentication Models
- `Token` - OAuth2 token response with access_token, token_type, and refresh_token
- `RefreshTokenRequest` - Request model for token refresh

### User Models  
- `CreateUser` - User registration model (username, email, password)
- `User` - Public user model (excludes sensitive data)
- `UserInDB` - Internal user model with hashed password
- `UpdateUser` - User update model for profile changes
- `UpdatePassword` - Password change model (current_password, new_password)

### Verification Models
- `SendVerificationRequest` - Email-only model for requesting verification codes
- `VerifyEmailRequest` - Email and code model for verification
- `UpdateForgottenPassword` - Password reset model (email, verification_code, new_password)

### Example Usage in Custom Routes

```python
from fastapiutils.models import CreateUser, User, VerifyEmailRequest
from pydantic import BaseModel

# Extend existing models
class ExtendedUser(User):
    phone_number: Optional[str] = None
    company: Optional[str] = None

# Create custom models following the same pattern
class CustomRequest(BaseModel):
    custom_field: str
    optional_field: Optional[int] = None
```

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
from fastapiutils.database_service import DatabaseService

router = APIRouter()

@router.get("/protected")
async def protected_route(
    current_user: CurrentActiveUser,
    db_service: DatabaseService = Depends(get_database_service)
):
    return {"user": current_user.username, "user_id": current_user.id}
```

## Internationalization

The package includes built-in English and German translations that are automatically loaded. You can add custom translations or override existing ones by setting the `LOCALES_DIR` environment variable:

```bash
# Set custom locales directory
LOCALES_DIR=./my_custom_locales
```

### How Translation Override Works

1. **Built-in locales** (en.json, de.json) are always loaded first
2. **Custom locales** from `LOCALES_DIR` are loaded second and can:
   - Override existing keys in built-in locales
   - Add new keys to existing locales  
   - Add completely new locales

**Example custom locale file** (`./my_custom_locales/en.json`):
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
- `RSA_KEYS_DIR`: Path to directory containing RSA key files
- `SMTP_SERVER`: SMTP server address (required for email verification)
- `SMTP_PORT`: SMTP server port (required for email verification)
- `SMTP_USER`: SMTP username/email (required for email verification)
- `SMTP_PASSWORD`: SMTP password/app password (required for email verification)

**Optional Environment Variables:**
- `DEFAULT_LOCALE`: Default language for i18n service (default: "en")
- `LOCALES_DIR`: Path to custom translation files directory
- `COLOR_CONFIG_FILE`: Path to custom color configuration for email templates
- `ENVIRONMENT`: Set to "development" to disable some security features

**Note**: Email configuration is mandatory as the system requires email verification for all new user registrations.

## Error Handling

The package raises appropriate HTTP exceptions with localized messages:

### Common Error Codes
- **400 Bad Request** - Invalid user data, expired/invalid verification codes
- **401 Unauthorized** - Invalid credentials, missing authentication
- **404 Not Found** - User not found, invalid verification code
- **409 Conflict** - Username/email already exists
- **500 Internal Server Error** - Database errors, email sending failures

### Security Features

#### Password Reset Security
- **Short Expiration**: Reset codes expire after 24 hours
- **Single Use**: Reset codes become invalid after use
- **Secure Hashing**: New passwords are securely hashed before storage

#### Email Change Security
- **Authentication Required**: User must be logged in to change email
- **New Email Verification**: Verification sent to new email address only
- **Uniqueness Validation**: Ensures new email isn't already in use
- **Atomic Updates**: Email only updated after successful verification

#### General Security
- **Rate Limiting**: 1-minute cooldown for verification code resends
- **Code Validation**: Strict 6-digit code format validation
- **Secure Storage**: All verification codes stored with timestamps
- **Localized Errors**: Error messages respect user's language preference

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

RSA_KEYS_DIR=/etc/ssl/jwt-keys

# Email configuration (REQUIRED for email verification)
SMTP_SERVER=smtp.your-domain.com
SMTP_PORT=587
SMTP_USER=noreply@your-domain.com
SMTP_PASSWORD=your-secure-smtp-password

# Optional production settings
DEFAULT_LOCALE=en
LOCALES_DIR=/opt/app/locales
COLOR_CONFIG_FILE=/opt/app/config/colors.json
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
app.include_router(user.router, prefix="/user", tags=["users"])

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
