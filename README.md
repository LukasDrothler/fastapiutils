# FastAPI Utils

A reusable FastAPI utilities package for authentication, user management, and database operations.

## Features

- JWT-based authentication with RSA256 encryption
- User registration and management
- Database utilities for MySQL
- Internationalization support
- Clean configuration classes
- Refresh token support

## Installation

```bash
pip install git+https://github.com/LukasDrothler/fastapiutils
```

## Quick Start

```python
from fastapi import FastAPI
from fastapiutils import AuthConfig, DatabaseConfig, AuthManager, create_auth_router, create_user_router

app = FastAPI()

# Configure database connection
db_config = DatabaseConfig(
    host="localhost",
    port=3306,
    user="root",
    password="your_password",
    database="your_database"
)

# Configure authentication settings
auth_config = AuthConfig(
    rsa_keys_path="/path/to/your/keys",
    access_token_expire_minutes=30,
    refresh_token_expire_days=30,
    algorithm="RS256",
    default_locale="en"
)

# Create auth manager
auth_manager = AuthManager(auth_config, db_config)

# Include routers
app.include_router(create_auth_router(auth_manager), prefix="/auth")
app.include_router(create_user_router(auth_manager), prefix="/api")
```

## Configuration

The package uses clean configuration classes for easy setup. See the documentation for detailed configuration options.
