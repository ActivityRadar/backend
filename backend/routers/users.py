from datetime import datetime
from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordRequestForm

import backend.util.errors as E
from backend.database.models.shared import PhotoInfo, PhotoUrl
from backend.database.models.users import (
    User,
    UserApiIn,
    UserApiOut,
    UserDetailed,
    UserRelation,
    VerifyUserInfo,
)
from backend.database.service import relation_service, user_service
from backend.routers.auth import (
    authenticate_user,
    get_current_user,
    get_user_by_name,
    login,
)
from backend.util.crypto import (
    ChangePasswordForm,
    ResetPasswordForm,
    ResetPasswordRequest,
)

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

me_router = APIRouter(
    prefix="/me",
    tags=["me"],
    dependencies=[
        Depends(get_current_user)
    ],  # only logged in users can access user data
)

photo_router = APIRouter(
    prefix="/photo",
    tags=["profile_photo"],
)

relation_router = APIRouter(
    prefix="/friends",
    tags=["friends"],
    dependencies=[
        Depends(get_current_user)
    ],  # only logged in users can access user data
)

ApiUser = Annotated[User, Depends(get_current_user)]


@me_router.get("/")
def get_this_user(user: ApiUser) -> UserDetailed:
    return UserDetailed(**user.dict())


@me_router.delete("/")
async def delete_user(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    success = await user_service.archive(user)
    if success:
        message = "User was archived! Will be deleted in 14 days!"
    else:
        message = "User could not be archived!"

    return {"message": message}


@me_router.put("/")
async def update_user(user: ApiUser, change_set: Annotated[dict, Body()]):
    try:
        new_info = await user_service.update_info(user, change_set)
    except E.InvalidUpdateOption as e:
        raise HTTPException(400, f"{e.option} is not a valid update option!")
    except:
        raise HTTPException(400, "Request encountered an error!")

    return {"message": "User data changed successfully!", "new_user_info": new_info}


@me_router.put("/change_password")
async def change_user_password(user: ApiUser, form_data: ChangePasswordForm = Body()):
    try:
        await user_service.change_password(user, form_data)
    except E.UserWrongPassword:
        raise HTTPException(403, "Wrong old password!")
    except E.UserNewPasswordIsOldPassword:
        raise HTTPException(403, "New and old password are same!")


@photo_router.post("/")
async def create_profile_photo(user: ApiUser, photo_url: PhotoUrl):
    photo_info = PhotoInfo(
        user_id=user.id, url=photo_url.url, creation_date=datetime.utcnow()
    )

    await user_service.put_photo(user=user, photo_info=photo_info)


@photo_router.get("/")
async def get_profile_photo(user: ApiUser):
    """
    This does not have to be implemented, as the user gets the photo info with the
    GET /users/me request anyways
    """

    raise NotImplementedError()


@photo_router.delete("/")
async def delete_profile_photo(user: ApiUser):
    await user_service.delete_photo(user)


@router.put("/{user_id}/report-avatar")
async def report_profile_photo(reporting_user: ApiUser, user_id: PydanticObjectId):
    reported = await user_service.get_by_id(user_id)
    if reported is None:
        raise HTTPException(400, "User does not exist!")

    await user_service.report_avatar(reporter=reporting_user, reported=reported)


@relation_router.post("/{user_id}")
async def add_as_friend(requester: ApiUser, user_id: PydanticObjectId):
    u = await user_service.get_by_id(user_id)
    if not u:
        raise HTTPException(404, "User does not exist!")

    try:
        f_id = await relation_service.add_friend(requester, u)
    except Exception as e:
        print(type(e))
        raise HTTPException(400, "Something went wrong!")

    return {
        "message": "Friend request sent!",
        "username": u.username,
        "relation_id": f_id,
    }


@relation_router.post("/accept/{relation_id}")
async def accept_friend_request(user: ApiUser, relation_id: PydanticObjectId):
    try:
        await relation_service.accept_friend_request(user, relation_id)
    except Exception as e:
        print(type(e))
        raise HTTPException(400, "Bad request!")

    return {"message": "Success!"}


@relation_router.post("/decline/{relation_id}")
async def decline_friend_request(user: ApiUser, relation_id: PydanticObjectId):
    try:
        await relation_service.decline_friend_request(user, relation_id)
    except Exception as e:
        print(type(e))
        raise HTTPException(400, "Bad request!")

    return {"message": "Success!"}


@relation_router.get("/")
async def get_all_friends(user: ApiUser) -> list[UserApiOut]:
    rs = relation_service.get_all_active_relations(user)
    users = await relation_service.relations_to_users(user, rs)
    return [UserApiOut(**u.dict()) for u in users]


@relation_router.get("/open")
async def get_received_friend_requests(user: ApiUser) -> list[UserRelation]:
    rs = await relation_service.get_received_requests(user)
    return rs


@router.post("/")
async def create_user(user_info: UserApiIn):
    # TODO: This should probably be protected with an API key.
    try:
        u = await user_service.create_user(user_info)
    except E.UserWithNameExists:
        raise HTTPException(403, "User with name exists!")

    return {"id": u.id}


@router.post("/verify")
async def verify_new_user(verify_info: VerifyUserInfo):
    try:
        return await user_service.verify(verify_info)
    except E.VerificationTimeout:
        raise HTTPException(404, "Verification timed out! Recreate the user!")
    except E.UserDoesNotExist:
        raise HTTPException(404, "User does not exist!")
    except E.AlreadyVerified:
        raise HTTPException(403, "User already verified!")
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/id")
async def get_user_infos(
    ids: list[PydanticObjectId] = Query(alias="q"),
) -> list[UserApiOut]:
    ids = list(set(ids))
    match len(ids):
        case 0:
            return []
        case 1:
            u = await user_service.get_by_id(ids[0])
            if not u:
                raise HTTPException(404, "User not found!")

            return [UserApiOut(**u.dict())]
        case _:
            us = await user_service.get_bulk_by_id(ids)
            return [UserApiOut(**u.dict()) for u in us]


@router.put("/reset_password")
async def request_reset_password(request_body: ResetPasswordRequest):
    try:
        await user_service.request_reset_password(request_body.email)
    except E.UserDoesNotExist:
        raise HTTPException(404, "User does not exist!")
    except E.UserHasPendingRequest:
        raise HTTPException(400, "User has pending request!")
    except E.EmailDoesNotMatchAccount:
        # Dont do anything, the potential attacker shouldnt know anything...
        pass

    return {
        "message": "If the E-mail address matched a user's, a request has been sent to it!"
    }


@router.put("/reset_password/{token}")
async def reset_password(token: str, reset_info: ResetPasswordForm = Body()):
    try:
        await user_service.execute_password_reset(token, reset_info)
    except E.TokenInvalid:
        raise HTTPException(401, "Token outdated or invalid!")
    except E.UserDoesNotExist:
        raise HTTPException(404, "User does not exist!")
    except E.UserNewPasswordDoesNotMatch:
        raise HTTPException(401, "Passwords don't match!")

    return {"message": "Password reset successfully!"}


@router.put("/reactivate")
async def unarchive_user(form_data: OAuth2PasswordRequestForm = Depends()):
    session_token_dict = await login(form_data)

    user = await get_user_by_name(form_data.username)
    if not user:
        raise HTTPException(404, "User does not exist!")

    success = await user_service.unarchive(user)
    if not success:
        raise HTTPException(400, "User is not archived!")

    return session_token_dict


@router.get("/")
async def find_users_by_name(search: Annotated[str, Query()]) -> list[UserApiOut]:
    users = await user_service.find_by_name(search)
    return [UserApiOut(**u.dict()) for u in users]


@router.get("/check-email")
async def check_email_taken(email: Annotated[str, Query()]) -> bool:
    """Returns true if the email is already in use."""
    u = await user_service.get_by_email(email)
    return u is not None


@router.post("/report/{user_id}")
def report_user(reporting_user: ApiUser, user_id: int):
    # TODO: implement
    # return {"message": "User reported successfully!", "user_id": user_id}
    pass


router.include_router(relation_router)
me_router.include_router(photo_router)
router.include_router(me_router)
