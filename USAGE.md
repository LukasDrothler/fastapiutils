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

## Usage Examples

### 1. Simple Setup with Environment Variables

Set these environment variables:
```bash
export RSA_KEYS_PATH="/path/to/keys"
export DB_HOST="localhost"
export DB_PORT="3306"
export DB_USER="root"
export DB_PASSWORD="your_password"
export DB_NAME="your_database"
export ACCESS_TOKEN_EXPIRE_MINUTES="30"
export REFRESH_TOKEN_EXPIRE_DAYS="30"
```

Then in your FastAPI app:

```python
from fastapi import FastAPI
from fastapiutils import create_auth_manager_from_env, create_auth_router, create_user_router

app = FastAPI()

# Create auth manager from environment variables
auth_manager = create_auth_manager_from_env()

# Include routers
app.include_router(create_auth_router(auth_manager), prefix="/auth")
app.include_router(create_user_router(auth_manager), prefix="/api")
```

### 2. Explicit Configuration

```python
from fastapi import FastAPI
from fastapiutils import create_auth_manager, create_auth_router, create_user_router

app = FastAPI()

# Create auth manager with explicit config
auth_manager = create_auth_manager(
    rsa_keys_path="/path/to/keys",
    db_host="localhost",
    db_user="root",
    db_password="password",
    db_database="mydb",
    access_token_expire_minutes=60,
    refresh_token_expire_days=7
)

# Include routers
app.include_router(create_auth_router(auth_manager), prefix="/auth")
app.include_router(create_user_router(auth_manager), prefix="/api")
```

### 3. Manual Configuration (Most Flexible)

```python
from fastapi import FastAPI
from fastapiutils import (
    AuthConfig, DatabaseConfig, AuthManager,
    create_auth_router, create_user_router
)

app = FastAPI()

# Configure database
db_config = DatabaseConfig(
    host="localhost",
    port=3306,
    user="root",
    password="password",
    database="mydb"
)

# Configure authentication
auth_config = AuthConfig(
    rsa_keys_path="/path/to/keys",
    access_token_expire_minutes=60,
    refresh_token_expire_days=7,
    algorithm="RS256",
    token_url="auth/token",  # Custom token URL
    default_locale="de"      # German as default
)

# Create auth manager
auth_manager = AuthManager(auth_config, db_config)

# Include routers with custom prefixes
app.include_router(create_auth_router(auth_manager), prefix="/auth")
app.include_router(create_user_router(auth_manager), prefix="/api/v1")
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
from fastapiutils import I18n

# Custom translations directory
i18n = I18n(locales_dir="./my_locales", default_locale="fr")

# Use in auth manager
auth_manager = AuthManager(auth_config, db_config, i18n=i18n)
```

## Error Handling

The package raises appropriate HTTP exceptions with localized messages:

- 400 Bad Request - Invalid user data
- 401 Unauthorized - Invalid credentials
- 409 Conflict - Username/email already exists
- 500 Internal Server Error - Database errors
