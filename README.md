# FastAPI Utils

A reusable FastAPI utilities package for authentication, user management, and database operations with email verification.

## Features

- JWT-based authentication with RSA256 encryption
- User registration with **mandatory email verification** (6-digit codes)
- Database utilities for MySQL with **automatic schema initialization**
- Email verification system with resend functionality
- **Customer forms management** (cancellations and feedback)
- **Stripe payment integration** with webhook handling and customer portal
- Internationalization support (English and German built-in)
- Environment variable-based configuration
- Dependency injection architecture
- Refresh token support
- Premium user levels
- **Admin user role management**

## Installation

```bash
pip install git+https://github.com/LukasDrothler/fastapiutils
```

## Prerequisites

### Database Setup

Create a MySQL database and run the provided SQL file to create the required tables:

**Important**: The database schema is now **automatically initialized** when the `DatabaseService` starts up. The library will execute the `requirements.sql` file to create all necessary tables including:

```sql
-- Use the provided requirements.sql file
-- Creates user table, verification_code table, and customer form tables

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

**Note**: You only need to create an empty MySQL database - all tables will be created automatically when the application starts.

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
RSA_KEYS_DIR=./keys

# Email configuration (REQUIRED for email verification)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Stripe configuration (OPTIONAL - for payment integration)
STRIPE_SECRET_API_KEY=sk_test_your_stripe_secret_key
STRIPE_SIGNING_SECRET=whsec_your_webhook_signing_secret
STRIPE_CONFIG_FILE=./config/custom_stripe.json
```

## Quick Start

```python
from fastapi import FastAPI
from fastapiutils import setup_dependencies
from fastapiutils.routers import auth, user, customer, stripe

app = FastAPI()

# Setup dependency injection container
setup_dependencies(
    access_token_expire_minutes=30, # Token expiration
    refresh_token_expire_days=30,   # Refresh token expiration
    token_url="token",              # Token endpoint URL
    private_key_filename="private_key.pem",  # RSA private key filename
    public_key_filename="public_key.pem"     # RSA public key filename
)

# Include built-in routers
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(customer.router)  # Customer forms management
app.include_router(stripe.router)    # Stripe payment integration
```

## Configuration

### setup_dependencies() Parameters

Configure the dependency injection container with the following parameters:

**Optional Parameters (with defaults):**
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
- `RSA_KEYS_DIR`: Path to directory containing RSA key files. If not found, new ones are generated
- `SMTP_SERVER`: SMTP server address (required for email verification)
- `SMTP_PORT`: SMTP server port (required for email verification)
- `SMTP_USER`: SMTP username/email (required for email verification)
- `SMTP_PASSWORD`: SMTP password/app password (required for email verification)

**Optional Environment Variables:**
- `DEFAULT_LOCALE`: Default language for i18n service (default: "en")
- `LOCALES_DIR`: Path to custom translation files directory
- `COLOR_CONFIG_FILE`: Path to custom color configuration for email templates
- `ENVIRONMENT`: Set to "development" to disable some security features
- `STRIPE_SECRET_API_KEY`: Stripe secret API key for payment processing
- `STRIPE_SIGNING_SECRET`: Stripe webhook signing secret for webhook verification
- `STRIPE_CONFIG_FILE`: Path to Stripe product configuration JSON file

**Note**: Email configuration is now **required** as the system uses mandatory email verification with 6-digit codes sent to users upon registration.

## API Endpoints

### Authentication Router

- `POST /token` - Login with username/password (supports optional `stay_logged_in` parameter)
- `POST /token/refresh` - Refresh access token using refresh token

### User Router

#### User Management
- `POST /user/register` - Register new user (sends 6-digit verification code via email)
- `GET /user/me` - Get current user profile
- `PUT /user/me` - Update current user information
- `PUT /user/me/password` - Change current user's password

#### Email Verification
- `POST /user/verify-email` - Verify email with 6-digit code
- `POST /user/resend-verification` - Resend verification code

#### Email Change
- `POST /user/me/email/change` - Request email change (sends verification code to new email)
- `POST /user/me/email/verify` - Verify new email with 6-digit code

#### Password Reset
- `POST /user/forgot-password/request` - Request password reset (sends verification code to email)
- `POST /user/forgot-password/verify` - Verify password reset code
- `POST /user/forgot-password/change` - Change password using verified reset code

#### Admin User Management
- `GET /user/all` - Get all users (admin only)
- `DELETE /user/{user_id}` - Delete user by ID (admin only)
- `POST /user/id-to-name-map` - Get username mapping for user IDs

### Customer Forms Router (Admin Only)

#### Cancellation Management
- `GET /forms/cancellation` - Get all cancellations (admin only)
- `POST /forms/cancellation` - Submit new cancellation request
- `PATCH /forms/cancellation/{cancellation_id}/archive` - Archive cancellation (admin only)

#### Feedback Management
- `GET /forms/feedback` - Get all feedback entries (admin only)
- `POST /forms/feedback` - Submit new feedback
- `PATCH /forms/feedback/{feedback_id}/archive` - Archive feedback (admin only)

### Stripe Router

#### Webhook Handling
- `POST /stripe-webhook` - Handle Stripe webhook events (checkout.session.completed, customer.subscription.deleted)

#### Customer Portal
- `POST /create-customer-portal-session` - Create Stripe customer portal session for subscription management (authenticated users only)

## Advanced Configuration

You can customize the setup with additional parameters:

```python
from fastapiutils import setup_dependencies

# Advanced configuration
setup_dependencies(
    access_token_expire_minutes=60,       # 1 hour access tokens
    refresh_token_expire_days=7,          # 1 week refresh tokens
    token_url="auth/token",               # Custom token endpoint
    private_key_filename="my_private.pem", # Custom key filenames
    public_key_filename="my_public.pem"
)
```

## Email Verification System

The library implements a **mandatory email verification system** using 6-digit codes. Users must verify their email address before they can fully access the platform.

### Email Verification Features

- **6-Digit Codes**: Secure, user-friendly verification codes
- **24-Hour Expiration**: Codes expire after 24 hours for security
- **Resend Functionality**: Users can request new codes with 1-minute cooldown
- **Single Use**: Codes become invalid after successful verification or reset
- **Localized Content**: Verification emails are localized based on user's preferred language
- **Database Tracking**: Verification status and timestamps are tracked
- **SMTP Support**: Works with any SMTP server (Gmail, Outlook, custom servers)

### Email Verification Flow

1. **User Registration**: User provides username, email, and password
2. **Code Generation**: System generates 6-digit code and stores in database
3. **Email Sent**: Verification code emailed to user
4. **User Verification**: User enters code via API endpoint
5. **Account Activation**: Email marked as verified, user can fully access platform
6. **Resend Option**: If code expired or mail was not received, the user can re-send a new code

## Email Templates

The library includes beautifully designed HTML email templates for all verification scenarios:

### Built-in Templates

- **`email_verification.html`** - Welcome email with verification code for new users
- **`forgot_password_verification.html`** - Password reset email with verification code  
- **`email_change_verification.html`** - Email change verification with code for new address

### Template Features

- **Responsive Design**: Works on all devices and email clients
- **Localized Content**: All text is automatically translated based on user locale
- **Customizable Colors**: Colors can be customized via `COLOR_CONFIG_FILE` environment variable
- **Brand Integration**: Supports custom app name, logo, and contact information
- **Security Focused**: Clear security warnings and expiration information

### Color Customization

Create a JSON file with custom colors and set the `COLOR_CONFIG_FILE` environment variable:

```json
{
  "primary_color": "#4f46e5",
  "secondary_color": "#7c3aed",
  "background_color": "#ffffff",
  "text_color": "#1f2937",
  "button_text_color": "#ffffff",
  "border_color": "#e5e7eb"
}
```

### Template Variables

All templates support these variables:
- `{app_name}` - Your application name
- `{app_owner}` - Your name/company
- `{contact_email}` - Support email address
- `{logo_url}` - Logo URL for branding
- Plus all localized content from translation files

## Stripe Payment Integration

The library includes a comprehensive Stripe integration for handling payments, subscriptions, and premium user management.

### Stripe Service Features

- **Webhook Event Handling**: Automatically processes Stripe webhook events
- **Premium Level Management**: Maps Stripe products to user premium levels
- **Customer Portal Integration**: Provides access to Stripe's customer portal
- **Subscription Management**: Handles subscription creation and cancellation
- **Secure Configuration**: Environment-based configuration with validation
- **Internationalization**: Localized error messages and responses

### Stripe Configuration

Set up the following environment variables for Stripe integration:

```bash
# Stripe API Configuration
STRIPE_SECRET_API_KEY=sk_test_your_stripe_secret_key
STRIPE_SIGNING_SECRET=whsec_your_webhook_signing_secret  
STRIPE_CONFIG_FILE=./config/custom_stripe.json
```

Create a Stripe configuration file (`custom_stripe.json`) to map your Stripe product IDs to premium levels:

```json
{
  "product_id_to_premium_level": {
    "prod_ABC123": 1,
    "prod_DEF456": 2,
    "prod_GHI789": 3
  }
}
```

### Supported Webhook Events

The Stripe service automatically handles these webhook events:

#### checkout.session.completed
- Triggered when a customer starts a subscription
- Updates user's premium level based on purchased product
- Associates Stripe customer ID with user account
- Validates session data and product mapping

#### customer.subscription.deleted
- Triggered when a subscription is cancelled
- Resets user's premium level to 0 (free tier)
- Maintains Stripe customer ID for future purchases

### Stripe API Endpoints

#### Webhook Endpoint
```python
POST /stripe-webhook
```
- Handles incoming Stripe webhook events
- Validates webhook signature for security
- Processes payment and subscription events
- Returns localized success/error messages

**Headers:**
- `Stripe-Signature`: Webhook signature (automatically provided by Stripe)

**Response Examples:**
```json
// Success
{
  "detail": "User with id 'user-123' has been updated to premium level 1."
}

// Error
{
  "detail": "Invalid product ID: prod_unknown"
}
```

#### Customer Portal Session
```python
POST /create-customer-portal-session
```
- Creates a Stripe customer portal session
- Allows users to manage their subscriptions
- Requires user authentication
- Returns portal URL for redirection

**Authentication:** Bearer token required

**Response:**
```json
{
  "id": "bps_1234567890",
  "object": "billing_portal.session",
  "url": "https://billing.stripe.com/session/bps_1234567890"
}
```

### Stripe Service Usage

The Stripe service is automatically available through dependency injection:

```python
from fastapi import APIRouter, Depends, Request
from fastapiutils.dependencies import get_stripe_service, get_i18n_service, get_database_service
from fastapiutils.stripe_service import StripeService
from fastapiutils.i18n_service import I18nService
from fastapiutils.database_service import DatabaseService
from fastapiutils import CurrentActiveUser

router = APIRouter()

@router.post("/custom-payment-endpoint")
async def handle_payment(
    request: Request,
    current_user: CurrentActiveUser,
    stripe_service: StripeService = Depends(get_stripe_service),
    i18n_service: I18nService = Depends(get_i18n_service),
    db_service: DatabaseService = Depends(get_database_service)
):
    locale = i18n_service.extract_locale_from_request(request)
    
    # Check if Stripe service is active
    if not stripe_service.is_active:
        raise HTTPException(
            status_code=503,
            detail=i18n_service.t("api.stripe.webhook.service_not_active", locale)
        )
    
    # Create customer portal session
    portal_session = await stripe_service.create_customer_portal_session(
        customer_id=current_user.stripe_customer_id,
        i18n_service=i18n_service,
        locale=locale
    )
    
    return {"portal_url": portal_session.url}
```

### Premium Level Management

The Stripe integration automatically manages user premium levels:

```python
# Premium levels are mapped in your Stripe configuration
{
  "product_id_to_premium_level": {
    "prod_basic": 1,      # Basic subscription
    "prod_pro": 2,        # Pro subscription  
    "prod_enterprise": 3  # Enterprise subscription
  }
}
```

When a user purchases a subscription:
1. Webhook receives `checkout.session.completed` event
2. System extracts product ID from session data
3. Maps product ID to premium level using configuration
4. Updates user's `premium_level` and `stripe_customer_id` in database
5. User gains access to premium features

### Error Handling and Validation

The Stripe service includes comprehensive error handling:

- **Configuration Validation**: Checks for required environment variables
- **Webhook Signature Verification**: Validates webhook authenticity
- **Product ID Validation**: Ensures products exist in configuration
- **User Validation**: Verifies user exists and is valid
- **Database Transaction Safety**: Handles database errors gracefully
- **Localized Error Messages**: Returns translated error messages

### Security Features

- **Webhook Signature Verification**: All webhooks are cryptographically verified
- **Environment Variable Configuration**: Sensitive keys stored securely
- **User Authentication**: Customer portal requires valid authentication
- **Database Integrity**: Foreign key constraints prevent orphaned records
- **Input Validation**: All Stripe data is validated before processing

## Password Reset Workflow

The package provides a secure password reset system using verification codes sent via email.

### Password Reset Features

- **Email-based Reset**: Reset codes sent to user's registered email address
- **6-Digit Codes**: Same secure format as email verification
- **24-Hour Expiration**: Reset codes expire after 24 hours
- **Single Use**: Reset codes become invalid after use
- **Localized Emails**: Reset emails are localized based on user's preferred language

### Password Reset Flow

1. **Request Reset**: User provides email address via `POST /user/forgot-password/request`
2. **Code Generation**: If email exists, system generates 6-digit reset code
3. **Email Sent**: Reset code emailed to user
4. **Verify Code**: User submits reset code via `POST /user/forgot-password/verify`
5. **Change Password**: User provides new password via `POST /user/forgot-password/change`
6. **Password Updated**: Password is securely hashed and updated in database

### Password Reset API Usage

```python
# 1. Request password reset
response = requests.post("http://localhost:8000/user/forgot-password/request", json={
    "email": "user@example.com"
})
# Returns: {"detail": "Password reset verification code has been sent to your email address"}

# 2. Verify reset code (user receives code via email)
response = requests.post("http://localhost:8000/user/forgot-password/verify", json={
    "email": "user@example.com",
    "code": "123456"
})
# Returns: {"detail": "Verification code verified successfully"}

# 3. Change password with verified code
response = requests.post("http://localhost:8000/user/forgot-password/change", json={
    "email": "user@example.com",
    "verification_code": "123456", 
    "new_password": "new_secure_password"
})
# Returns: {"detail": "Password updated successfully"}
```

## Email Change Workflow

Users can securely change their email address using a verification-based system.

### Email Change Features

- **New Email Verification**: Verification code sent to the new email address
- **Security Validation**: Ensures new email is unique and properly formatted
- **6-Digit Codes**: Consistent with other verification systems
- **24-Hour Expiration**: Verification codes expire after 24 hours
- **Authenticated Process**: User must be logged in to change email
- **Atomic Updates**: Email only updated after successful verification

### Email Change Flow

1. **Request Change**: Authenticated user provides new email via `POST /user/me/email/change`
2. **Validation**: System validates new email format and uniqueness
3. **Code Generation**: System generates 6-digit verification code
4. **Email Sent**: Verification code sent to the new email address
5. **Verify New Email**: User submits verification code via `POST /user/me/email/verify`
6. **Email Updated**: User's email address is updated in the database

### Email Change API Usage

```python
# Headers with authentication token
headers = {"Authorization": "Bearer your_access_token"}

# 1. Request email change (sends code to new email)
response = requests.post("http://localhost:8000/user/me/email/change", 
    headers=headers,
    json={"email": "newemail@example.com"}
)
# Returns: {"detail": "Verification code sent to your new email address. Please check your email."}

# 2. Verify new email with code (received via email)
response = requests.post("http://localhost:8000/user/me/email/verify",
    headers=headers, 
    json={
        "email": "newemail@example.com",
        "code": "123456"
    }
)
# Returns: {"detail": "Email address updated successfully"}
```

### Email Verification Translation

The email verification content is automatically translated based on the user's locale. The following translation keys are used:

**Email Verification:**
- `email.email_verification.subject`: Email subject line for verification
- `email.email_verification.email_title`: Email title for verification 
- `email.email_verification.content.*`: Various email content fields (supports parameter interpolation)
- `api.auth.verification.verification_code_expired`: Error message when verification code is expired
- `api.auth.verification.invalid_verification_code`: Error message when verification code is invalid
- `api.auth.verification.verification_code_already_used`: Error message when code already used
- `api.auth.verification.resend_cooldown`: Error message when trying to resend too soon
- `api.auth.verification.verification_code_resent`: Success message when verification code is resent
- `api.email.email_sending_failed`: Error message when email sending fails

**Password Reset:**
- `email.forgot_password_verification.subject`: Subject for password reset emails
- `email.forgot_password_verification.content.*`: Password reset email content
- `api.auth.forgot_password.forgot_password_verification_code_sent`: Confirmation message

**Email Change:**
- `email.email_change_verification.subject`: Subject for email change verification
- `email.email_change_verification.content.*`: Email change email content
- `api.auth.email_change.email_change_verification_sent`: Confirmation message
- `api.auth.email_change.email_change_verified_successfully`: Success message

## Custom Routers

Create custom routers using dependency injection. The services are automatically injected through FastAPI's dependency system.

Example custom router (`routers/pet.py`):

```python
from fastapi import APIRouter, Depends, Request, Path, HTTPException, status
from typing import Annotated
from fastapiutils import User, CurrentActiveUser
from fastapiutils.dependencies import get_database_service, get_i18n_service
from fastapiutils.database_service import DatabaseService
from fastapiutils.i18n_service import I18nService
from .models import Pet  # Your custom models

"""Create the router for pet-related endpoints"""
router = APIRouter()

@router.get("/pet/{pet_id}", response_model=Pet, tags=["pets"])
async def get_pet(
    current_user: CurrentActiveUser,
    pet_id: str = Path(description="The ID of the pet to retrieve"),
    request: Request = None,
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service),
):
    """Usage of the dependency injection pattern"""
    locale = i18n_service.extract_locale_from_request(request)
    
    # Validate pet_id length (example with parameter interpolation)
    if len(pet_id) > 36:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=i18n_service.t("pet.id_too_long", locale, 
                        max_length=36, 
                        current_length=len(pet_id)),
        )
    
    """Retrieve a specific pet by ID for the current user"""
    sql = "SELECT * FROM pet WHERE id = %s AND user_id = %s"
    result = db_service.execute_single_query(sql, (pet_id, current_user.id))
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=i18n_service.t("pet.pet_not_found", locale),
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
from fastapiutils.dependencies import get_i18n_service
from fastapiutils.i18n_service import I18nService
from fastapi import Depends, Request

# In your route handler
async def my_route(
    request: Request,
    i18n_service: I18nService = Depends(get_i18n_service)
):
    # Extract locale from request headers
    locale = i18n_service.extract_locale_from_request(request)
    
    # Use parameter interpolation in translations
    message = i18n_service.t("pet.name_too_long", locale, max_length=50, current_length=75)
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
from fastapiutils.dependencies import get_i18n_service
from fastapiutils.i18n_service import I18nService

async def validate_name(
    name: str, 
    locale: str
    i18n_service: I18nService = Depends(get_i18n_service)
) -> str:
    """Validate pet name field with internationalized error messages"""
    if not name or not name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=i18n_service.t("pet.name_required", locale),
        )
    
    cleaned_name = name.strip()
    MAX_NAME_LENGTH = 50
    if len(cleaned_name) > MAX_NAME_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=i18n_service.t("pet.name_too_long", locale, 
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

You can override or extend the built-in translations by setting the `LOCALES_DIR` environment variable:

```bash
# Set custom locales directory
LOCALES_DIR=./my_custom_locales
```

Custom locale files will be merged with built-in translations, allowing you to:
- Override existing translations
- Add new translation keys
- Support additional languages

Example custom locale file (`./my_custom_locales/en.json`):
```json
{
  "pet": {
    "name_too_long": "Pet name must be {max_length} characters or less (current: {current_length})",
    "species_invalid": "Pet species must be one of: {valid_species} (current: {current_species})"
  }
}
```

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
# Database configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=your_database

# RSA Keys
RSA_KEYS_DIR=./keys

# Email configuration (required)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Optional customization
DEFAULT_LOCALE=en
LOCALES_DIR=./custom_locales
COLOR_CONFIG_FILE=./config/colors.json
ENVIRONMENT=development

# Stripe configuration (optional)
STRIPE_SECRET_API_KEY=sk_test_your_stripe_secret_key
STRIPE_SIGNING_SECRET=whsec_your_webhook_signing_secret
STRIPE_CONFIG_FILE=./config/custom_stripe.json
```

```python
from dotenv import load_dotenv

load_dotenv()  # This loads the .env file automatically
```

## Module Structure

The library is organized into specialized modules for better maintainability:

### Core Modules

- **`auth_service.py`** - Authentication and JWT token management
- **`database_service.py`** - Database connection and query execution with automatic schema initialization
- **`mail_service.py`** - Email sending with HTML template support
- **`i18n_service.py`** - Internationalization and translation management
- **`dependencies.py`** - Dependency injection container and service factories
- **`customer_form_service.py`** - Customer forms management (cancellations and feedback)
- **`stripe_service.py`** - Stripe payment integration and webhook handling

### Data and Validation Modules

- **`models.py`** - Pydantic models for requests and responses
- **`user_queries.py`** - Database queries for user operations
- **`user_validators.py`** - User data validation functions
- **`verification_queries.py`** - Database queries for verification codes

### Feature Modules

- **`email_verification.py`** - Email verification workflow functions
- **`routers/`** - FastAPI router modules
  - `token.py` - Token endpoints
  - `user.py` - User management endpoints
  - `customer.py` - Customer forms management endpoints (admin-only access)
  - `stripe.py` - Stripe payment and webhook endpoints

### Resources

- **`locales/`** - Translation files (en.json, de.json)
- **`templates/`** - HTML email templates
- **`config/`** - Default color configuration
- **`requirements.sql`** - Database schema

## Available Dependencies

The following dependency functions are available for injection into your route handlers:

### Service Dependencies
- `get_auth_service()` - Returns the AuthService instance
- `get_database_service()` - Returns the DatabaseService instance  
- `get_mail_service()` - Returns the MailService instance
- `get_i18n_service()` - Returns the I18nService instance
- `get_customer_form_service()` - Returns the CustomerFormService instance
- `get_stripe_service()` - Returns the StripeService instance

### User Authentication Dependencies
- `CurrentUser` - Type annotation for getting the current authenticated user
- `CurrentActiveUser` - Type annotation for getting the current active (non-disabled) user
- `CurrentAdminUser` - Type annotation for getting the current admin user (requires is_admin=True)

Example using service dependencies:

```python
from fastapi import Depends, APIRouter
from fastapiutils.dependencies import get_database_service, get_i18n_service, get_customer_form_service
from fastapiutils.database_service import DatabaseService
from fastapiutils.i18n_service import I18nService
from fastapiutils.customer_form_service import CustomerFormService
from fastapiutils import CurrentAdminUser

router = APIRouter()

@router.get("/custom-endpoint")
async def custom_endpoint(
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service)
):
    # Use services directly
    result = db_service.execute_query("SELECT * FROM some_table")
    message = i18n_service.t("some.translation.key", "en")
    return {"data": result, "message": message}

@router.get("/admin-only-endpoint")
async def admin_endpoint(
    current_admin: CurrentAdminUser,
    customer_service: CustomerFormService = Depends(get_customer_form_service),
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service)
):
    # Admin-only endpoint example
    cancellations = customer_service.get_cancellations(
        db_service=db_service,
        i18n_service=i18n_service,
        locale="en"
    )
    return {"cancellations": cancellations}
```
