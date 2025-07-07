from auth_utils import *
from db_user import *
from models import *
from i18n import get_i18n, extract_locale_from_header
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional, Annotated
from datetime import datetime, timedelta, timezone
import jwt
from jwt.exceptions import InvalidTokenError

router = APIRouter()

# Global I18n instance
i18n = get_i18n()


def create_bearer_token(data: dict, isRefresh: bool = False):
    to_encode = data.copy()
    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    if isRefresh:
        expires_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, PRIVATE_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request,
    stay_logged_in: Optional[bool] = False
) -> Token:
    locale = extract_locale_from_header(request.headers.get("accept-language"))
    
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=i18n.t("auth.incorrect_credentials", locale),
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_bearer_token(data={"sub": user.username})
    if stay_logged_in:
        refresh_token = create_bearer_token(data={"sub": user.username}, isRefresh=True)
        return Token(access_token=access_token, refresh_token=refresh_token)
    
    return Token(access_token=access_token)


@router.post("/token/refresh")
async def refresh_access_token(
    current_user: Annotated[User, Depends(get_current_active_user)],
    refresh_request: RefreshTokenRequest,
    request: Request,
) -> Token:
    locale = extract_locale_from_header(request.headers.get("accept-language"))
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=i18n.t("auth.could_not_validate_credentials", locale),
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(refresh_request.refresh_token, PUBLIC_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    if token_data.username != current_user.username:
        raise credentials_exception

    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    
    access_token = create_bearer_token(data={"sub": user.username})
    return Token(access_token=access_token, token_type="bearer")