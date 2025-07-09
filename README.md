# FastAPI Utils

A reusable FastAPI utilities package for authentication, user management, and database operations.

## Features

- JWT-based authentication with RSA256 encryption
- User registration and management
- Database utilities for MySQL
- Email notifications (welcome emails on registration)
- Internationalization support (English and German built-in)
- Simple configuration approach
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

## Quick Start

```python
from fastapi import FastAPI
from fastapiutils import FastapiContext, AuthConfig, DatabaseConfig, create_auth_router, create_user_router
from routers import pet

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
    mail_config=mail_config,  # Optional: Enable welcome emails
    default_locale="en"
)

# Include routers
app.include_router(create_auth_router(fa_context))
app.include_router(create_user_router(fa_context))
# Include custom routers (see later paragraph for explanation)
app.include_router(pet.create_router(fa_context))
```

## Configuration

### FastapiContext Parameters

- `auth_config`: AuthConfig object containing authentication settings
- `database_config`: DatabaseConfig object containing database connection settings
- `mail_config`: MailConfig object containing email settings (optional)
- `custom_locales_dir`: Custom locales directory (optional)
- `default_locale`: Default language (default: "en")

### AuthConfig Parameters

- `rsa_keys_path`: Path to directory containing RSA key files (required)
- `access_token_expire_minutes`: Access token expiration (default: 30)
- `refresh_token_expire_days`: Refresh token expiration (default: 30)
- `token_url`: Token endpoint URL (default: "token")
- `private_key_filename`: Private key filename (default: "private_key.pem")
- `public_key_filename`: Public key filename (default: "public_key.pem")

### DatabaseConfig Parameters

- `host`: Database host (required)
- `port`: Database port (required)
- `user`: Database username (required)
- `password`: Database password (required)
- `database`: Database name (required)

### MailConfig Parameters (Optional)

- `smtp_server`: SMTP server address (required if mail_config is provided)
- `smtp_port`: SMTP server port (required if mail_config is provided)
- `smtp_user`: SMTP username/email (required if mail_config is provided)
- `smtp_password`: SMTP password/app password (required if mail_config is provided)

**Note**: When `mail_config` is provided, users will receive welcome emails upon registration with localized content.

## API Endpoints

### Authentication Router

- `POST /token` - Login with username/password
- `POST /token/refresh` - Refresh access token

### User Router (`/users`)

- `POST /users/register` - Register new user
- `GET /users/me` - Get current user profile

## Usage with Environment Variables

```python
import os
from fastapiutils import FastapiContext, AuthConfig, DatabaseConfig, MailConfig

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

# Optional: Create mail configuration
mail_config = None
if os.getenv("SMTP_SERVER"):
    mail_config = MailConfig(
        smtp_server=os.getenv("SMTP_SERVER"),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_user=os.getenv("SMTP_USER"),
        smtp_password=os.getenv("SMTP_PASSWORD")
    )

fa_context = FastapiContext(
    auth_config=auth_config,
    database_config=database_config,
    mail_config=mail_config,
    default_locale=os.getenv("DEFAULT_LOCALE", "en")
)
```

## Email Configuration

The library supports sending welcome emails to users upon registration. This is optional and can be configured using the `MailConfig` object.

### Email Features

- **Welcome Emails**: Automatically sent when users register
- **Localized Content**: Email content is localized based on user's preferred language
- **Error Handling**: Graceful handling of email sending failures
- **SMTP Support**: Works with any SMTP server (Gmail, Outlook, custom servers)

### Common SMTP Configurations

**Gmail:**
```python
mail_config = MailConfig(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    smtp_user="your_email@gmail.com",
    smtp_password="your_app_password"  # Use App Password, not regular password
)
```

**Outlook:**
```python
mail_config = MailConfig(
    smtp_server="smtp-mail.outlook.com",
    smtp_port=587,
    smtp_user="your_email@outlook.com",
    smtp_password="your_password"
)
```

**Custom SMTP Server:**
```python
mail_config = MailConfig(
    smtp_server="mail.yourcompany.com",
    smtp_port=587,
    smtp_user="noreply@yourcompany.com",
    smtp_password="your_smtp_password"
)
```

### Email Content Translation

The welcome email content is automatically translated based on the user's locale. The following translation keys are used:

- `auth.welcome_email_subject`: Email subject line
- `auth.welcome_email_content`: Email body content (supports `{username}` parameter)
- `auth.email_sending_failed`: Error message when email sending fails

## Custom routers

Create a custom router by defining a function that returns an APIRouter.
Make sure to give the FastapiContext as a parameter.

In this example we define a create_router function in routers/pet.py

```python
from fastapiutils import FastapiContext, User
from fastapiutils.i18n import extract_locale_from_header
from core.basemodels import Pet
from core.db_pet import get_pet_by_id
from fastapi import APIRouter, Depends, Request, Path, HTTPException, status
from typing import Annotated

def create_router(fa_context: FastapiContext) -> APIRouter:
    """Create the router for pet-related endpoints"""
    router = APIRouter()
    """Get dependency function to ensure an active user is making the request"""
    get_current_user_dep, get_current_active_user_dep = fa_context.create_dependency_functions()

    @router.get("/pet/{pet_id}", response_model=Pet, tags=["pets"])
    async def get_pet(
        current_user: Annotated[User, Depends(get_current_active_user_dep)],
        pet_id: str = Path(description="The ID of the pet to retrieve"),
        request: Request = None,
    ):
        """Usage of the internationalization utility with parameter interpolation"""
        locale = extract_locale_from_header(request.headers.get("accept-language"))
        
        # Validate pet_id length (example with parameter interpolation)
        if len(pet_id) > 36:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=fa_context.i18n.t("pet.id_too_long", locale, 
                                       max_length=36, 
                                       current_length=len(pet_id)),
            )
        
        """Retrieve a specific pet by ID for the current user by using the database utility"""
        sql = "SELECT * FROM pet WHERE id = %s AND user_id = %s"
        result = fa_context.db_manager.execute_single_query(sql, (pet_id, current_user.id))
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=fa_context.i18n.t("pet.pet_not_found", locale),
            )
        return Pet(**result)

    return router
```

## Internationalization (i18n) with Parameter Interpolation

The library now supports parameter interpolation in translation strings, allowing you to pass dynamic values into your translations.

### Basic Usage

```python
from fastapiutils.i18n import extract_locale_from_header

# Extract locale from request headers
locale = extract_locale_from_header(request.headers.get("accept-language"))

# Use parameter interpolation in translations
fa_context.i18n.t("pet.name_too_long", locale, max_length=50, current_length=75)
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
def validate_name(fa_context: FastapiContext, name: str, locale: str = "en") -> str:
    """Validate pet name field with internationalized error messages"""
    if not name or not name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=fa_context.i18n.t("pet.name_required", locale),
        )
    
    cleaned_name = name.strip()
    if len(cleaned_name) > MAX_NAME_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=fa_context.i18n.t("pet.name_too_long", locale, 
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
fa_context = FastapiContext(
    # ... other parameters ...
    custom_locales_dir="/path/to/your/custom/locales"
)
```

Custom locale files will be merged with built-in translations, allowing you to:
- Override existing translations
- Add new translation keys
- Support additional languages
