# FastAPI Utils

A reusable FastAPI utilities package for authentication, user management, and database operations.

## Features

- JWT-based authentication with RSA256 encryption
- User registration and management
- Database utilities for MySQL
- Internationalization support
- Simple configuration approach
- Refresh token support

## Installation

```bash
pip install git+https://github.com/LukasDrothler/fastapiutils
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

The package uses direct parameters for easy setup. See the documentation for detailed configuration options.
