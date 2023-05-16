from typing import Annotated
from fastapi import APIRouter, Body, Depends, HTTPException

from backend.database.models.users import UserIn
from backend.database.service.users import UserService
from backend.routers.auth import authenticate_user, get_current_user, get_user_by_name, login
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


router.include_router(me_router)

@router.post("/")
async def create_user(user_info: UserIn):
    try:
        u_id = await user_service.create_user(user_info)
    except:
        raise HTTPException(400, "User with name exists!")

    return { "id": u_id }

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
