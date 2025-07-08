"""
Example usage of the fastapiutils package

This example shows the configuration approach using direct parameters.
"""
from fastapi import FastAPI
from fastapiutils import (
    FastapiContext, 
    create_auth_router, create_user_router
)

# Create FastAPI app
app = FastAPI(title="FastAPI Utils Example")

# Create auth manager with direct parameters
fa_context = FastapiContext(
    rsa_keys_path="/path/to/your/keys",  # Update this path
    db_host="localhost",
    db_port=3306,
    db_user="root",
    db_password="your_password",
    db_name="your_database",
    access_token_expire_minutes=30,
    refresh_token_expire_days=30,
    token_url="token",
    default_locale="en"
    # custom_locales_dir="./my_locales",  # Optional: add custom/override translations
)

# Include default routers
app.include_router(create_auth_router(fa_context))
app.include_router(create_user_router(fa_context))
# Include custom routers
# app.include_router(custom.create_router(fa_context))

@app.get("/")
async def root():
    return {"message": "FastAPI Utils Example", "version": "0.1.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
