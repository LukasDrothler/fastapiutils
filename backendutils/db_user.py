from models import CreateUser, UserInDB
from mysql_utils import generate_uuid, execute_single_query, execute_modification_query
from i18n import get_i18n
from fastapi import HTTPException, status
from typing import Optional
from datetime import datetime, timezone
from passlib.context import CryptContext

import re

# Global I18n instance
i18n = get_i18n()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(username: Optional[str] = None, email: Optional[str] = None) -> Optional[UserInDB]:
    result = None
    if username and email:
        result = execute_single_query(
            "SELECT * FROM user WHERE LOWER(username) = LOWER(%s) AND LOWER(email) = LOWER(%s)", 
            (username, email)
        )
    elif email:
        result = execute_single_query(
            "SELECT * FROM user WHERE LOWER(email) = LOWER(%s)", 
            (email,)
        )
    elif username:
        result = execute_single_query(
            "SELECT * FROM user WHERE LOWER(username) = LOWER(%s)", 
            (username,)
        )
    
    if result:
        return UserInDB(**result)
    return None


def check_new_user_is_valid(user: CreateUser, locale: str = "en"):
    if not re.match(r"^\w{3,}$", user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=i18n.t("auth.username_invalid", locale),
        )
    if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=i18n.t("auth.email_invalid", locale),
        )
    if len(user.password) < 8 or not re.search(r"[A-Z]", user.password) or not re.search(r"[0-9]", user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=i18n.t("auth.password_weak", locale),
        )
    
    if get_user(username=user.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=i18n.t("auth.username_taken", locale),
        )
    if get_user(email=user.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=i18n.t("auth.email_taken", locale),
        )
    return


def create_db_user( user: CreateUser, locale: str = "en"):
    check_new_user_is_valid(user, locale)
    uid = generate_uuid("user")
    if uid is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=i18n.t("auth.user_creation_failed", locale),
        )
    hashed_password=get_password_hash(user.password)

    execute_modification_query(
        "INSERT INTO user (id, username, email, hashed_password) VALUES (%s, %s, %s, %s)",
        (uid, user.username, user.email, hashed_password)
    )
    return {"msg": i18n.t("auth.user_created", locale)}


def authenticate_user(username: str, password: str):
    user = get_user(username=username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    current_time = datetime.now(timezone.utc)
    execute_modification_query(
        "UPDATE user SET last_seen = %s WHERE id = %s", 
        (current_time, user.id)
    )
    return user
