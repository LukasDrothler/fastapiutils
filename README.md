# FastAPI Utils

A reusable FastAPI utilities package for authentication, user management, and database operations.

## Features

- JWT-based authentication with RSA256 encryption
- User registration and management
- Database utilities for MySQL
- Email notifications (welcome emails on registration)
- Internationalization support (English and German built-in)
- Environment variable-based configuration
- Dependency injection architecture
- Refresh token support
- Premium user levels

## Installation

```bash
pip install git+https://github.com/LukasDrothler/fastapiutils
```

## Prerequisites

### Database Setup

Create a MySQL database and run the provided SQL file to create the user table:

```sql
-- Use the provided user.sql file
-- The table includes unique constraints for username and email
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

Set up the following environment variables:

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

**Optional Environment Variables:**
```bash
# Email configuration (optional - for welcome emails)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

## Quick Start

```python
from fastapi import FastAPI
from fastapiutils import setup_dependencies
from fastapiutils.routers import auth, user

app = FastAPI()

# Setup dependency injection container
setup_dependencies(
    custom_locales_dir=None,        # Optional: path to custom translations
    default_locale="en",            # Default language
    access_token_expire_minutes=30, # Token expiration
    refresh_token_expire_days=30,   # Refresh token expiration
    token_url="token",              # Token endpoint URL
    private_key_filename="private_key.pem",  # RSA private key filename
    public_key_filename="public_key.pem"     # RSA public key filename
)

# Include built-in routers
app.include_router(auth.router)
app.include_router(user.router)
```

## Configuration

### setup_dependencies() Parameters

Configure the dependency injection container with the following parameters:

**Optional Parameters (with defaults):**
- `custom_locales_dir`: Custom locales directory for additional/override translations (default: None)
- `default_locale`: Default language (default: "en")
- `access_token_expire_minutes`: Access token expiration in minutes (default: 30)
- `refresh_token_expire_days`: Refresh token expiration in days (default: 30)
- `token_url`: Token endpoint URL (default: "token")
- `private_key_filename`: Private key filename (default: "private_key.pem")
- `public_key_filename`: Public key filename (default: "public_key.pem")

### Environment Variables

**Required Environment Variables:**
- `DB_HOST`: Database host
- `DB_PORT`: Database port
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password
- `DB_NAME`: Database name
- `RSA_KEYS_PATH`: Path to directory containing RSA key files

**Optional Environment Variables (for email functionality):**
- `SMTP_SERVER`: SMTP server address
- `SMTP_PORT`: SMTP server port
- `SMTP_USER`: SMTP username/email
- `SMTP_PASSWORD`: SMTP password/app password

**Note**: When email environment variables are provided, users will receive welcome emails upon registration with localized content.

## API Endpoints

### Authentication Router

- `POST /token` - Login with username/password
- `POST /token/refresh` - Refresh access token

### User Router

- `POST /users/register` - Register new user
- `GET /users/me` - Get current user profile

## Advanced Configuration

You can customize the setup with additional parameters:

```python
from fastapiutils import setup_dependencies

# Advanced configuration
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

## Email Configuration

The library supports sending welcome emails to users upon registration. This is optional and requires setting up SMTP environment variables.

### Email Features

- **Welcome Emails**: Automatically sent when users register
- **Localized Content**: Email content is localized based on user's preferred language
- **Error Handling**: Graceful handling of email sending failures
- **SMTP Support**: Works with any SMTP server (Gmail, Outlook, custom servers)

### Common SMTP Configurations

**Gmail (.env file):**
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password  # Use App Password, not regular password
```

**Outlook (.env file):**
```bash
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USER=your_email@outlook.com
SMTP_PASSWORD=your_password
```

**Custom SMTP Server (.env file):**
```bash
SMTP_SERVER=mail.yourcompany.com
SMTP_PORT=587
SMTP_USER=noreply@yourcompany.com
SMTP_PASSWORD=your_smtp_password
```

### Email Content Translation

The welcome email content is automatically translated based on the user's locale. The following translation keys are used:

- `auth.welcome_email_subject`: Email subject line
- `auth.welcome_email_content`: Email body content (supports `{username}` parameter)
- `auth.email_sending_failed`: Error message when email sending fails

## Custom Routers

Create custom routers using dependency injection. The services are automatically injected through FastAPI's dependency system.

Example custom router (`routers/pet.py`):

```python
from fastapi import APIRouter, Depends, Request, Path, HTTPException, status
from typing import Annotated
from fastapiutils import User, CurrentActiveUser
from fastapiutils.dependencies import DatabaseServiceDependency, I18nServiceDependency
from .models import Pet  # Your custom models

"""Create the router for pet-related endpoints"""
router = APIRouter()

@router.get("/pet/{pet_id}", response_model=Pet, tags=["pets"])
async def get_pet(
    current_user: CurrentActiveUser,
    pet_id: str = Path(description="The ID of the pet to retrieve"),
    request: Request = None,
    db_service: DatabaseServiceDependency,
    i18n_service: I18nServiceDependency,
):
    """Usage of the dependency injection pattern"""
    locale = i18n_service.extract_locale_from_header(request.headers.get("accept-language"))
    
    # Validate pet_id length (example with parameter interpolation)
    if len(pet_id) > 36:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=i18n.t("pet.id_too_long", locale, 
                        max_length=36, 
                        current_length=len(pet_id)),
        )
    
    """Retrieve a specific pet by ID for the current user"""
    sql = "SELECT * FROM pet WHERE id = %s AND user_id = %s"
    result = db_service.execute_single_query(sql, (pet_id, current_user.id))
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=i18n.t("pet.pet_not_found", locale),
        )
    return Pet(**result)

# In your main app
from routers import pet
app.include_router(pet.router)
```

## Internationalization (i18n) with Parameter Interpolation

The library supports parameter interpolation in translation strings, allowing you to pass dynamic values into your translations.

### Basic Usage

```python
from fastapiutils.dependencies import I18nServiceDependency
from fastapi import Depends, Request

# In your route handler
async def my_route(
    request: Request,
    i18n_service: I18nServiceDependency
):
    # Extract locale from request headers
    locale = i18n_service.extract_locale_from_header(request.headers.get("accept-language"))
    
    # Use parameter interpolation in translations
    message = i18n.t("pet.name_too_long", locale, max_length=50, current_length=75)
    # Returns: "Pet name must be 50 characters or less (current: 75)"
```

### Translation File Format

Translation files support Python string formatting with named parameters:

```json
{
  "pet": {
    "name_too_long": "Pet name must be {max_length} characters or less (current: {current_length})",
    "species_invalid": "Pet species must be one of: {valid_species} (current: {current_species})",
    "weight_too_high": "Pet weight must be {max_weight} kg or less (current: {current_weight})"
  }
}
```

### Validation Example

```python
from fastapi import HTTPException, status, Depends
from fastapiutils.dependencies import I18nServiceDependency

async def validate_name(
    name: str, 
    locale: str = "en",
    i18n_service: I18nServiceDependency
) -> str:
    """Validate pet name field with internationalized error messages"""
    if not name or not name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=i18n.t("pet.name_required", locale),
        )
    
    cleaned_name = name.strip()
    MAX_NAME_LENGTH = 50
    if len(cleaned_name) > MAX_NAME_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=i18n.t("pet.name_too_long", locale, 
                         max_length=MAX_NAME_LENGTH, 
                         current_length=len(cleaned_name)),
        )
    
    return cleaned_name
```

### Error Handling

The i18n system gracefully handles missing parameters and formatting errors:

- If a parameter is missing, the translation will still work but the placeholder will remain
- If formatting fails, the original unformatted string is returned
- If a translation key is missing, it falls back to the default locale
- If the key is still missing, the key itself is returned

### Custom Locales

You can override or extend the built-in translations by providing a custom locales directory:

```python
from fastapiutils import setup_dependencies

setup_dependencies(
    custom_locales_dir="/path/to/your/custom/locales",
    # ... other parameters ...
)
```

Custom locale files will be merged with built-in translations, allowing you to:
- Override existing translations
- Add new translation keys
- Support additional languages

## Complete Example

See the `example.py` file for a complete working example that includes:

- Environment variable loading with `python-dotenv`
- Dependency injection setup
- Router inclusion
- Development server configuration

To run the example:

1. Copy `.env.example` to `.env` and configure your settings
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python example.py`

## Using with .env Files

For easier configuration management, use a `.env` file:

```bash
# Copy the example file
cp .env.example .env

# Edit the .env file with your configuration
# Then in your Python code:
```

```python
from dotenv import load_dotenv

load_dotenv()  # This loads the .env file automatically
```

## Available Dependencies

The following dependency functions and type annotations are available for injection into your route handlers:

### Service Dependencies (Preferred - Type Annotations)
- `AuthServiceDependency` - Type annotation for injecting the AuthService instance
- `DatabaseServiceDependency` - Type annotation for injecting the DatabaseService instance  
- `MailServiceDependency` - Type annotation for injecting the MailService instance (or None if not configured)
- `I18nServiceDependency` - Type annotation for injecting the I18nService instance

### Legacy Service Dependencies (Functions)
- `get_auth_service()` - Returns the AuthService instance
- `get_database_service()` - Returns the DatabaseService instance  
- `get_mail_service()` - Returns the MailService instance (or None if not configured)
- `get_i18n_service()` - Returns the I18nService instance

### User Authentication Dependencies
- `CurrentUser` - Type annotation for getting the current authenticated user
- `CurrentActiveUser` - Type annotation for getting the current active (non-disabled) user

Example using service dependencies (recommended approach):

```python
from fastapi import APIRouter
from fastapiutils.dependencies import DatabaseServiceDependency, I18nServiceDependency

router = APIRouter()

@router.get("/custom-endpoint")
async def custom_endpoint(
    db_service: DatabaseServiceDependency,
    i18n_service: I18nServiceDependency
):
    # Use services directly
    result = db_service.execute_query("SELECT * FROM some_table")
    message = i18n.t("some.translation.key", "en")
    return {"data": result, "message": message}
```
