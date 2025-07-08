# FastAPI Utils

A reusable FastAPI utilities package for authentication, user management, and database operations.

## Features

- JWT-based authentication with RSA256 encryption
- User registration and management
- Database utilities for MySQL
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
from fastapiutils import FastapiContext, create_auth_router, create_user_router
from routers import pet

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
# Include custom routers (see later paragraph for explanation)
app.include_router(pet.create_router(fa_context))
```

## Configuration

### Required Parameters

- `rsa_keys_path`: Path to directory containing RSA key files
- `db_host`: Database host
- `db_port`: Database port
- `db_user`: Database username
- `db_password`: Database password
- `db_name`: Database name

### Optional Parameters

- `access_token_expire_minutes`: Access token expiration (default: 30)
- `refresh_token_expire_days`: Refresh token expiration (default: 30)
- `token_url`: Token endpoint URL (default: "token")
- `default_locale`: Default language (default: "en")
- `custom_locales_dir`: Custom locales directory (default: None)
- `private_key_filename`: Private key filename (default: "private_key.pem")
- `public_key_filename`: Public key filename (default: "public_key.pem")

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
from fastapiutils import FastapiContext

fa_context = FastapiContext(
    rsa_keys_path=os.getenv("RSA_KEYS_PATH", "/path/to/keys"),
    db_host=os.getenv("DB_HOST", "localhost"),
    db_port=int(os.getenv("DB_PORT", "3306")),
    db_user=os.getenv("DB_USER", "root"),
    db_password=os.getenv("DB_PASSWORD", ""),
    db_name=os.getenv("DB_NAME", ""),
)
```

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
        """Usage of the internationalization utility"""
        locale = extract_locale_from_header(request.headers.get("accept-language"))
        """Retrieve a specific pet by ID for the current user by using the database utility"""
        sql = "SELECT * FROM pet WHERE id = %s AND user_id = %s"
        result = fa_context.execute_single_query(sql, (pet_id, current_user.id))
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=fa_context.i18n.t("pet.pet_not_found", locale),
            )
        return Pet(**result)

    return router
```
