"""
Example usage of the fastapiutils package

This example shows three different ways to set up the authentication:
1. Using environment variables
2. Using explicit configuration
3. Using factory functions
"""
from fastapi import FastAPI
from fastapiutils import (
    AuthConfig, DatabaseConfig, AuthManager, 
    create_auth_router, create_user_router,
    create_auth_manager_from_env, create_auth_manager
)

# Create FastAPI app
app = FastAPI(title="FastAPI Utils Example")

# Method 1: Using environment variables (recommended for production)
# Requires these environment variables to be set:
# RSA_KEYS_PATH, DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, etc.
try:
    auth_manager = create_auth_manager_from_env()
    print("✓ Using environment variables for configuration")
except Exception as e:
    print(f"✗ Could not create auth manager from env: {e}")
    
    # Method 2: Using explicit configuration (good for development)
    auth_manager = create_auth_manager(
        rsa_keys_path="/path/to/your/keys",  # Update this path
        db_host="localhost",
        db_port=3306,
        db_user="root",
        db_password="your_password",
        db_database="your_database",
        access_token_expire_minutes=30,
        refresh_token_expire_days=30,
        default_locale="en"
    )
    print("✓ Using explicit configuration")


db_config = DatabaseConfig(
    host="localhost",
    port=3306,
    user="root",
    password="your_password",
    database="your_database"
)

auth_config = AuthConfig(
    rsa_keys_path="/path/to/your/keys",
    access_token_expire_minutes=30,
    refresh_token_expire_days=30,
    algorithm="RS256",
    default_locale="en"
)

auth_manager = AuthManager(auth_config, db_config)

# Include routers
app.include_router(create_auth_router(auth_manager), prefix="/auth", tags=["auth"])
app.include_router(create_user_router(auth_manager), prefix="/api", tags=["users"])

@app.get("/")
async def root():
    return {"message": "FastAPI Utils Example", "version": "0.1.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
