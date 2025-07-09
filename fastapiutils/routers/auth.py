from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional, Annotated
from jwt.exceptions import InvalidTokenError
import jwt

from fastapiutils.auth_service import AuthService
from fastapiutils.database_service import DatabaseService
from fastapiutils.i18n_service import I18nService

from ..models import Token, RefreshTokenRequest, TokenData
from ..dependencies import get_auth_service, get_database_service, get_i18n_service

"""Create authentication router with dependency injection"""
router = APIRouter()

@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service),
    stay_logged_in: Optional[bool] = False
) -> Token:
    locale = i18n_service.extract_locale_from_header(request.headers.get("accept-language"))
    
    user = auth_service.authenticate_user(form_data.username, form_data.password, db_service=db_service)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=i18n_service.t("auth.incorrect_credentials", locale),
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_service.create_bearer_token(username=user.username)
    if stay_logged_in:
        refresh_token = auth_service.create_bearer_token(username=user.username, is_refresh=True)
        return Token(access_token=access_token, refresh_token=refresh_token)
    
    return Token(access_token=access_token)

@router.post("/token/refresh")
async def refresh_access_token(
    refresh_request: RefreshTokenRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service),
) -> Token:
    locale = i18n_service.extract_locale_from_header(request.headers.get("accept-language"))
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=i18n_service.t("auth.could_not_validate_credentials", locale),
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(refresh_request.refresh_token, auth_service.public_key, algorithms=[auth_service.algorithm])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    
    # Get and validate current user
    user = auth_service.get_user(username=token_data.username, db_service=db_service)
    if user is None or user.disabled:
        raise credentials_exception
    
    access_token = auth_service.create_bearer_token(username=user.username)
    return Token(access_token=access_token, token_type="bearer")