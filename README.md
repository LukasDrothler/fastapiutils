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

For detailed usage instructions, see `USAGE.md`.
