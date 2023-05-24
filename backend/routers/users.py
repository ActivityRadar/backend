from fastapi import APIRouter, HTTPException

from backend.database.models.users import UserIn
from backend.database.service.users import UserService

router = APIRouter(
    prefix = "/users",
    tags = ["users"]
)

me_router = APIRouter(
    prefix = "/me"
)

user_service = UserService()

@me_router.get("/")
def get_this_user():
    return {"user_id": "This is you!"}

@me_router.delete("/")
def delete_user():
    return {"message": "User was archived. Finally deleted in 14 days!"}

@me_router.put("/")
def update_user(data: dict):
    return {"message": "User data changed successfully!"}


router.include_router(me_router)

@router.post("/")
async def create_user(user_info: UserIn):
    try:
        u_id = await user_service.create_user(user_info)
    except:
        raise HTTPException(400, "User with name exists!")

    return { "id": u_id }

@router.get("/{user_id}")
def get_user_info(user_id: int):
    return {"user_id": user_id}

@router.post("/report/{user_id}")
def report_user(user_id: int):
    return {"message": "User reported successfully!", "user_id": user_id}

@router.post("/friend/{user_id}")
def add_as_friend(user_id: int):
    return {"message": "Friend request sent!", "user_id": user_id}
