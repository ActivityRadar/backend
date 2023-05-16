from typing import Annotated
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from backend.database.models.users import User, UserAPI, UserIn
from backend.database.service.users import UserService
from backend.routers.auth import authenticate_user, get_current_user, get_user_by_name, login
from backend.util.auth import ChangePasswordForm, ResetPasswordForm
import backend.util.errors as E

router = APIRouter(
    prefix = "/users",
    tags = ["users"]
)

me_router = APIRouter(
    prefix = "/me"
)

user_service = UserService()

ApiUser = Annotated[User, Depends(get_current_user)]

@me_router.get("/")
def get_this_user():
    return {"user_id": "This is you!"}

@me_router.delete("/")
async def delete_user(user: ApiUser, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    await authenticate_user(form_data.username, form_data.password)
    success = await user_service.archive(user)
    if success:
        message = "User was archived! Will be deleted in 14 days!"
    else:
        message = "User could not be archived!"

    return { "message": message }

@me_router.put("/")
async def update_user(user: ApiUser, change_set: Annotated[dict, Body()]):
    try:
        new_info = await user_service.update_info(user, change_set)
    except:
        raise HTTPException(400, "Request encountered an error!")

    return {
        "message": "User data changed successfully!",
        "new_user_info": new_info
    }

@me_router.put("/change_password")
async def change_user_password(user: ApiUser, form_data: Annotated[ChangePasswordForm, Depends()]):
    print(form_data)
    try:
        await user_service.change_password(user, form_data)
    except:
        raise HTTPException(400, "Something went wrong!")

    print("Pw changed!")


router.include_router(me_router)

@router.post("/")
async def create_user(user_info: UserIn):
    try:
        u_id = await user_service.create_user(user_info)
    except:
        raise HTTPException(400, "User with name exists!")

    return { "id": u_id }

@router.get("/reset_password/{username}")
async def request_reset_password(username: str):
    try:
        await user_service.request_reset_password(username)
    except E.UserDoesNotExist:
        raise HTTPException(404, "User does not exist!")
    except E.UserHasPendingRequest:
        raise HTTPException(400, "User has pending request!")

    return { "message": f"A request has been sent to the user's email address!" }

@router.put("/reset_password/{token}")
async def reset_password(token: str, passwords: ResetPasswordForm):
    try:
        await user_service.execute_password_reset(token, passwords)
    except E.TokenInvalid:
        raise HTTPException(401, "Token outdated or invalid!")
    except E.UserDoesNotExist:
        raise HTTPException(404, "User does not exist!")
    except E.UserNewPasswordDoesNotMatch:
        raise HTTPException(401, "Passwords don't match!")

    return { "message": "Password reset successfully!" }

@router.put("/reactivate")
async def unarchive_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    session_token_dict = await login(form_data)

    user = await get_user_by_name(form_data.username)
    if not user:
        raise HTTPException(404, "User does not exist!")

    success = await user_service.unarchive(user)
    if not success:
        raise HTTPException(400, "User is not archived!")

    return session_token_dict

@router.get("/{user_id}")
def get_user_info(user_id: int):
    return {"user_id": user_id}

@router.post("/report/{user_id}")
def report_user(user_id: int):
    return {"message": "User reported successfully!", "user_id": user_id}

@router.post("/friend/{user_id}")
def add_as_friend(user_id: int):
    return {"message": "Friend request sent!", "user_id": user_id}
