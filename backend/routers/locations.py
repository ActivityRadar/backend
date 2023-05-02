from typing import Annotated
from fastapi import APIRouter, Query

from backend.database.models.shared import Review

from ..database.models.locations import Location

from ..util.types import LongitudeCoordinate, LatitudeCoordinate

router = APIRouter(
    prefix = "/locations",
    tags = ["locations"]
)

#### Locations

@router.get("/bbox")
def get_locations_by_bbox(
        west: LongitudeCoordinate,
        south: LatitudeCoordinate,
        east: LongitudeCoordinate,
        north: LatitudeCoordinate,
        activities: list[str] | None = Query(None)) -> list[Location]:
    return []
    # return {
    #     "bbox": [west, south, east, north],
    #     "activities": activities or "all"
    # }

@router.get("/around")
def get_locations_around(
        long: LongitudeCoordinate,
        lat: LatitudeCoordinate,
        radius: Annotated[float, "Distance in km"],
        activities: list[str] | None = Query(None)) -> list[Location]:
    return []
    # return {
    #     "center": [long, lat],
    #     "radius": radius or 0.0,
    #     "activities": activities or "all"
    # }

@router.get("/{location_id}")
def get_location(location_id: int, q: str | None = None) -> Location:
    return None
    # return {"location_id": location_id, "q": q}

@router.post("/")
def create_new_location(new_data: dict):
    pass

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
