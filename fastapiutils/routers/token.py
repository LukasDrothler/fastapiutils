from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from jwt.exceptions import InvalidTokenError
import jwt

from ..user_queries import UserQueries
from ..auth_service import AuthService
from ..database_service import DatabaseService
from ..i18n_service import I18nService
from ..models import LoginCredentials, Token, RefreshTokenRequest, TokenData
from ..dependencies import get_auth_service, get_database_service, get_i18n_service

"""Create authentication router with dependency injection"""
router = APIRouter()

@router.post("/token", response_model=Token, tags=["tokens"])
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service),
    stay_logged_in: bool = Query(False, description="Whether to issue a refresh token")
) -> Token:
    locale = i18n_service.extract_locale_from_request(request)
    return auth_service.get_token_for_user(
        username_or_email=form_data.username,
        password=form_data.password,
        db_service=db_service,
        i18n_service=i18n_service,
        locale=locale,
        stay_logged_in=stay_logged_in
    )


@router.post("/token/refresh", response_model=Token, tags=["tokens"])
async def refresh_access_token(
    refresh_request: RefreshTokenRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service),
) -> Token:
    locale = i18n_service.extract_locale_from_request(request)
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=i18n_service.t("api.auth.credentials.could_not_validate_credentials", locale),
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(refresh_request.refresh_token, auth_service.public_key, algorithms=[auth_service.algorithm])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except InvalidTokenError:
        raise credentials_exception
    
    # Get and validate current user
    user = UserQueries.get_user_by_id(token_data.user_id, db_service=db_service)
    if user is None or user.disabled:
        raise credentials_exception
    
    access_token = auth_service.create_bearer_token(
        user=user,
        db_service=db_service
        )
    return Token(access_token=access_token)