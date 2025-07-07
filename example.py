"""
Example usage of the fastapiutils package

This example shows the clean configuration approach using AuthConfig and DatabaseConfig classes.
"""
from fastapi import FastAPI
from fastapiutils import (
    AuthConfig, DatabaseConfig, AuthManager, 
    create_auth_router, create_user_router
)

# Create FastAPI app
app = FastAPI(title="FastAPI Utils Example")

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
    rsa_keys_path="/path/to/your/keys",  # Update this path
    access_token_expire_minutes=30,
    refresh_token_expire_days=30,
    token_url="token",
    algorithm="RS256",
    default_locale="en"
)

# Create auth manager with the configurations
auth_manager = AuthManager(auth_config, db_config)

# Include routers
app.include_router(create_auth_router(auth_manager))
app.include_router(create_user_router(auth_manager))

@app.get("/")
async def root():
    return {"message": "FastAPI Utils Example", "version": "0.1.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
