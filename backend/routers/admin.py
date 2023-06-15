from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends

from backend.database.models.users import User
from backend.routers.auth import get_admin

Admin = Annotated[User, Depends(get_admin)]

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(get_admin)])


@router.put("/locations/revert-update/{update_id}")
async def revert_location_update(admin: Admin, update_id: PydanticObjectId):
    pass
