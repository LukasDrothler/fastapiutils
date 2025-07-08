"""
Example usage of the fastapiutils package

This example shows the configuration approach using AuthConfig, DatabaseConfig, and MailConfig objects.
"""
from fastapi import FastAPI
from fastapiutils import (
    FastapiContext, AuthConfig, DatabaseConfig, MailConfig,
    create_auth_router, create_user_router
)

# Create FastAPI app
app = FastAPI(title="FastAPI Utils Example")

# Create configuration objects
auth_config = AuthConfig(
    rsa_keys_path="/path/to/your/keys",  # Update this path
    access_token_expire_minutes=30,
    refresh_token_expire_days=30,
    token_url="token"
)

database_config = DatabaseConfig(
    host="localhost",
    port=3306,
    user="root",
    password="your_password",
    database="your_database"
)

# Optional: Create mail configuration for welcome emails
mail_config = MailConfig(
    smtp_server="smtp.gmail.com",        # Update with your SMTP server
    smtp_port=587,
    smtp_user="your_email@gmail.com",    # Update with your email
    smtp_password="your_app_password"    # Update with your app password
)

# Create FastAPI context with configuration objects
fa_context = FastapiContext(
    auth_config=auth_config,
    database_config=database_config,
    mail_config=mail_config,             # Optional: Enable welcome emails
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
    return {"message": "FastAPI Utils Example", "version": "0.2.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
