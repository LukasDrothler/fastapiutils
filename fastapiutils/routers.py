from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional, Annotated
from jwt.exceptions import InvalidTokenError
import jwt

from .fastapi_context import FastapiContext
from .models import Token, CreateUser, User, RefreshTokenRequest, TokenData
from .i18n import extract_locale_from_header


def create_auth_router(fa_context: FastapiContext) -> APIRouter:
    """Create authentication router"""
    router = APIRouter()
    
    # Get dependency functions
    get_current_user_dep, get_current_active_user_dep = fa_context.create_dependency_functions()
    
    @router.post(f"/{fa_context.auth_config.token_url}")
    async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        request: Request,
        stay_logged_in: Optional[bool] = False
    ) -> Token:
        locale = extract_locale_from_header(request.headers.get("accept-language"))
        
        user = fa_context.authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=fa_context.i18n.t("auth.incorrect_credentials", locale),
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = fa_context.create_bearer_token(data={"sub": user.username})
        if stay_logged_in:
            refresh_token = fa_context.create_bearer_token(data={"sub": user.username}, is_refresh=True)
            return Token(access_token=access_token, refresh_token=refresh_token)
        
        return Token(access_token=access_token)
    
    @router.post(f"/{fa_context.auth_config.token_url}/refresh")
    async def refresh_access_token(
        current_user: Annotated[User, Depends(get_current_active_user_dep)],
        refresh_request: RefreshTokenRequest,
        request: Request,
    ) -> Token:
        locale = extract_locale_from_header(request.headers.get("accept-language"))
        
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=fa_context.i18n.t("auth.could_not_validate_credentials", locale),
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(refresh_request.refresh_token, fa_context.public_key, algorithms=[fa_context.auth_config.algorithm])
            username = payload.get("sub")
            if username is None:
                raise credentials_exception
            token_data = TokenData(username=username)
        except InvalidTokenError:
            raise credentials_exception
        
        if token_data.username != current_user.username:
            raise credentials_exception

        user = fa_context.get_user(username=token_data.username)
        if user is None:
            raise credentials_exception
        
        access_token = fa_context.create_bearer_token(data={"sub": user.username})
        return Token(access_token=access_token, token_type="bearer")
    
    return router


def create_user_router(fa_context: FastapiContext) -> APIRouter:
    """Create user management router"""
    router = APIRouter()
    
    # Get dependency functions
    get_current_user_dep, get_current_active_user_dep = fa_context.create_dependency_functions()
    
    @router.post("/users/register", status_code=201, tags=["users"])
    async def create_user(
        user: CreateUser,
        request: Request,
    ):
        locale = extract_locale_from_header(request.headers.get("accept-language"))
        return fa_context.create_user(user, locale)
    
    @router.get("/users/me", response_model=User, tags=["users"])
    async def read_users_me(
        current_user: Annotated[User, Depends(get_current_active_user_dep)],
    ):
        return current_user
    
    return router
