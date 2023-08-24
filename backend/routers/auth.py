from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

import backend.util.errors as errors
from backend.database.models.users import User
from backend.database.service import user_service
from backend.util.constants import REFRESH_TOKEN_EXPIRY_TIME
from backend.util.crypto import (
    create_refresh_token,
    decode_session_token,
    refresh_access_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


class AccessTokenBody(BaseModel):
    access_token: str
    token_type: str


class LoginTokenBody(AccessTokenBody):
    refresh_token: str


async def get_user(id: PydanticObjectId) -> User | None:
    return await user_service.get_by_id(id)


async def get_user_by_name(username: str) -> User | None:
    return await user_service.get_by_username(username)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    try:
        token_data = decode_session_token(token)
    except:
        raise HTTPException(400, "Invalid token!")

    user = await get_user(token_data.id)
    if user is None:
        raise HTTPException(400, "User not found!")

    return user


ApiUser = Annotated[User, Depends(get_current_user)]


async def get_admin(user: ApiUser):
    if user.admin is None or not user.admin:
        raise HTTPException(401, "User not authorized as admin!")

    return user


async def authenticate_user(username: str, plain: str) -> User:
    auth_exception = HTTPException(400, "Incorrect details!")
    user = await get_user_by_name(username)
    if not user:
        raise auth_exception

    if not verify_password(plain, user.authentication.password_hash):
        raise auth_exception

    return user


@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> LoginTokenBody:
    user = await authenticate_user(form_data.username, form_data.password)

    if user.archived_until is not None:
        raise HTTPException(403, f"User is archived until {user.archived_until}")

    refresh_token = create_refresh_token(
        data={"sub": str(user.id)}, expiry_time=REFRESH_TOKEN_EXPIRY_TIME
    )

    await user_service.set_refresh_token(user, refresh_token)

    token = refresh_access_token(
        data={"sub": str(user.id)}, refresh_token=refresh_token
    )

    return LoginTokenBody(
        access_token=token, refresh_token=refresh_token, token_type="bearer"
    )


@router.post("/refresh")
async def get_new_access_token(refresh_token: str) -> AccessTokenBody:
    user = await get_current_user(refresh_token)

    if user.archived_until is not None:
        raise HTTPException(403, f"User is archived until {user.archived_until}")

    if (
        user.authentication.refresh_token is None
        or user.authentication.refresh_token != refresh_token
    ):
        raise HTTPException(401, "Token invalid! Login needed!")

    token = refresh_access_token(
        data={"sub": str(user.id)}, refresh_token=refresh_token
    )

    return AccessTokenBody(access_token=token, token_type="bearer")


@router.post("/logout")
async def logout(user: ApiUser):
    try:
        await user_service.delete_refresh_token(user)
    except errors.UserAlreadyLoggedOut:
        raise HTTPException(401, "User logged out already!")
