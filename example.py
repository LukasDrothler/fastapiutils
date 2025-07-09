"""
Example usage of the fastapiutils package with dependency injection
"""
from fastapi import FastAPI
from fastapiutils.routers import user, auth
import os
from dotenv import load_dotenv
from fastapiutils import setup_dependencies

load_dotenv()

# Create FastAPI app
app = FastAPI(title="FastAPI Utils Example")

# Setup dependency injection container
setup_dependencies(
    custom_locales_dir=None,
    default_locale="en",
    access_token_expire_minutes=30,
    refresh_token_expire_days=30,
    token_url="token",
    private_key_filename="private_key.pem",
    public_key_filename="public_key.pem"
)

# Include routers (no need to pass auth_service anymore!)
app.include_router(auth.router)
app.include_router(user.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("example:app", host="localhost", port=int(os.getenv("FASTAPI_PORT", 8000)), log_level="info", reload=True)