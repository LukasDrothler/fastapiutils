from fastapi import APIRouter, Depends, Request
from fastapiutils import AuthService

from ..models import CreateUser, User
from ..i18n_service import extract_locale_from_header
from ..dependencies import get_auth_service
from ..dependencies import CurrentActiveUser

"""Create user management router with dependency injection"""
router = APIRouter()

@router.post("/users/register", status_code=201, tags=["users"])
async def create_user(
    user: CreateUser,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    locale = extract_locale_from_header(request.headers.get("accept-language"))
    return auth_service.create_user(user, locale)

@router.get("/users/me", response_model=User, tags=["users"])
async def read_users_me(
    current_user: CurrentActiveUser,
):
    return current_user