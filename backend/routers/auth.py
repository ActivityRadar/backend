from typing import Annotated
from beanie import PydanticObjectId

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from backend.database.models.users import User, UserAPI
from backend.database.service.users import UserService
from backend.util.auth import create_access_token, decode_session_token, verify_password

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
user_service = UserService()

async def get_user(id: PydanticObjectId) -> User | None:
    return await user_service.get_by_id(id)

async def get_user_by_name(username: str) -> User | None:
    return await user_service.get_by_username(username)

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        token_data = decode_session_token(token)
    except:
        raise HTTPException(400, "Invalid token!")

    user = await get_user(token_data.id)
    if user is None:
        raise HTTPException(400, "User not found!")

    return user

async def authenticate_user(username: str, plain: str):
    user = await get_user_by_name(username)
    if not user:
        raise HTTPException(400, "Incorrect details!")

    if not verify_password(plain, user.authentication.password_hash):
        raise HTTPException(400, "Incorrect details!")

    return user

@router.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = await authenticate_user(form_data.username, form_data.password)
    token = create_access_token(data={ "sub": str(user.id) })

    return { "access_token": token, "token_type": "bearer" }

@router.get("/users/me")
async def get_me(user: Annotated[User, Depends(get_current_user)]) -> UserAPI:
    return UserAPI(**user.dict())
