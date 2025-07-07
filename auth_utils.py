from db_user import get_user
from models import TokenData, User
from i18n import get_i18n
from fastapi import  Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from jwt.exceptions import InvalidTokenError
from cryptography.hazmat.primitives import serialization

import jwt
import os

def load_rsa_key(key_type: str):
    keys_path = os.getenv('RSA_KEYS_PATH')
    key_file_path = os.path.join(keys_path, f"{key_type}_key.pem")
    with open(key_file_path, 'rb') as key_file:
        if key_type == "private":
            return serialization.load_pem_private_key(key_file.read(), password=None)
        elif key_type == "public":
            return serialization.load_pem_public_key(key_file.read())
        else:
            raise ValueError("Invalid key type specified")

PUBLIC_KEY = load_rsa_key("public")
PRIVATE_KEY = load_rsa_key("private")
ALGORITHM = "RS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30

# Global I18n instance
i18n = get_i18n()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=i18n.t("auth.could_not_validate_credentials"),
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail=i18n.t("auth.inactive_user"))
    return current_user