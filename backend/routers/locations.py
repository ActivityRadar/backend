from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, Query

from backend.database.models.shared import Review
from backend.database.service.users import UserService
from backend.routers.users import ApiUser
from backend.util.errors import UserDoesNotExist, UserLowTrust

from ..database.models.locations import (
    LocationDetailed,
    LocationDetailedAPI,
    LocationNew,
    LocationShortAPI,
    LocationShortDB,
)
from ..database.service.locations import LocationService
from ..util.types import LatitudeCoordinate, LongitudeCoordinate

router = APIRouter(
    prefix = "/locations",
    tags = ["locations"]
)

location_service = LocationService()
user_service = UserService()

@router.get("/bbox")
async def get_locations_by_bbox(
        west: LongitudeCoordinate,
        south: LatitudeCoordinate,
        east: LongitudeCoordinate,
        north: LatitudeCoordinate,
        activities: list[str] | None = Query(None)) -> list[LocationShortAPI]:
    bbox = ((west, south), (east, north))
    short: list[LocationShortDB] = await location_service.get_bbox_short(bbox, activities)
    result: list[LocationShortAPI] = [LocationShortAPI(**loc.dict()) for loc in short]
    return result

@router.get("/around")
async def get_locations_around(
        long: LongitudeCoordinate,
        lat: LatitudeCoordinate,
        radius: Annotated[float, "Distance in km"],
        activities: list[str] | None = Query(None)) -> list[LocationShortAPI]:
    center = (long, lat)
    short = await location_service.get_around(center, radius, activities)
    result: list[LocationShortAPI] = [LocationShortAPI(**loc.dict()) for loc in short]
    return result

@router.get("/{location_id}")
async def get_location(location_id: PydanticObjectId) -> LocationDetailedAPI:
    result = await location_service.get(location_id)
    if result is None:
        raise HTTPException(404, detail=f"No location with {location_id=} exists!")
    return LocationDetailedAPI(**result.dict())

@router.post("/")
async def create_new_location(adding_user: ApiUser, info: LocationNew):
    try:
        trust_score = await user_service.check_eligible_to_add(adding_user.id)
    except UserDoesNotExist:
        raise HTTPException(400, "User does not exist!")
    except UserLowTrust:
        raise HTTPException(403, "User not trusted enough!")

    detailed = LocationDetailed(**info.dict(), recent_reviews=[], trust_score=trust_score)
    new_id = await location_service.insert(detailed, adding_user.id)
    return { "id": new_id }

@router.put("/{location_id}")
def update_location(location_id: int):
    # error if location not found

    # error if user has no rights to update location

    # error if data is incomplete

    pass

@router.delete("/{location_id}")
def delete_location(location_id: int):
    # error if location not found

    # error if user has no rights to remove location

    pass

#### REVIEWS

review_router = APIRouter(
    prefix = "/{location_id}/reviews",
    tags = ["reviews"]
)

@review_router.get("/")
def get_reviews(location_id: int, start: int, n: int) -> list[Review]:
    """
    Get `n` reviews starting from the `start`th entry.
    """
    return []

@review_router.post("/")
def create_review(location_id: int, data: dict):
    # error if location not found

    # error if user has review for location already

    # error if data is incomplete or incorrect

    pass

@review_router.put("/")
def update_review(location_id: int, review_id: int, data: dict):
    # error if location not found

    # error if review doesnt exist

    # error if review isnt owned by user

    # error if data is inclomplete or incorrect

    # error if location and review dont match
    pass

@review_router.put("/confirmation")
def set_confirmation(location_id: int, data: dict):
    # error if location not found

    # error if user has same confirmation for location already

    # error if data is inclomplete or incorrect

    pass

@review_router.delete("/")
def remove_review(location_id: int):
    # error if location not found

    pass

@review_router.put("/{review_id}")
def report_review(location_id: int, review_id: int, reason: str):
    # error if location not found

    # error if review does not exist

    pass

router.include_router(review_router)
