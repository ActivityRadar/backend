from fastapi import APIRouter

router = APIRouter(
    prefix = "/users",
    tags = ["users"]
)

me_router = APIRouter(
    prefix = "/me"
)

@me_router.get("/")
def get_this_user():
    return {"user_id": "This is you!"}

@me_router.delete("/")
def delete_user():
    return {"message": "User was archived. Finally deleted in 14 days!"}

@me_router.put("/")
def update_user(data: dict):
    return {"message": "User data changed successfully!"}


router.include_router(router)

@router.post("/")
def create_user(data: dict):
    return {"user_id": 0}

@router.get("/{user_id}")
def get_user_info(user_id: int):
    return {"user_id": user_id}

@router.post("/report/{user_id}")
def report_user(user_id: int):
    return {"message": "User reported successfully!", "user_id": user_id}

@router.post("/friend/{user_id}")
def add_as_friend(user_id: int):
    return {"message": "Friend request sent!", "user_id": user_id}
