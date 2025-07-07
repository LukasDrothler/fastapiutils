
from models import CreateUser, User
from db_user import create_db_user
from routers.auth import get_current_active_user
from i18n import extract_locale_from_header
from fastapi import APIRouter, Depends, Request
from typing import Annotated

router = APIRouter()

@router.post("/users/register", status_code=201, tags=["users"])
async def create_user(
    user: CreateUser,
    request: Request,
):
    return create_db_user(user, extract_locale_from_header(request.headers.get("accept-language")))


@router.get("/users/me", response_model=User, tags=["users"])
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user