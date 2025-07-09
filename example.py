"""
Example usage of the fastapiutils package
"""
from fastapi import FastAPI
import os
from dotenv import load_dotenv
from fastapiutils import (FastapiContext, create_auth_router, create_user_router)

load_dotenv()

# Create FastAPI app
app = FastAPI(title="FastAPI Utils Example")


# Create FastAPI context with configuration objects
fa_context = FastapiContext()

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("example:app", host="localhost", port=os.getenv("FASTAPI_PORT", 8000), log_level="info", reload=True)