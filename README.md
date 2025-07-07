# FastAPI Utils

A reusable FastAPI utilities package for authentication, user management, and database operations.

## Features

- JWT-based authentication with RSA256 encryption
- User registration and management
- Database utilities for MySQL
- Internationalization support
- Configurable auth settings
- Refresh token support

## Installation

```bash
pip install git+https://github.com/LukasDrothler/fastapiutils
```

## Quick Start

```python
from fastapi import FastAPI
from fastapiutils import AuthConfig, AuthManager, create_auth_router, create_user_router

app = FastAPI()

# Configure authentication
auth_config = AuthConfig(
    rsa_keys_path="/path/to/keys",
    access_token_expire_minutes=30,
    refresh_token_expire_days=30,
    algorithm="RS256"
)

# Create auth manager
auth_manager = AuthManager(auth_config)

# Include routers
app.include_router(create_auth_router(auth_manager), prefix="/auth")
app.include_router(create_user_router(auth_manager), prefix="/api")
```

## Configuration

See the documentation for detailed configuration options.
