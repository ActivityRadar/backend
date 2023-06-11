from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, Query

from backend.database.models.locations import (
    LocationDetailed,
    LocationDetailedAPI,
    LocationHistoryIn,
    LocationNew,
    LocationShortAPI,
    LocationShortDB,
    ReviewInfo,
    ReviewOut,
    ReviewsPage,
)
from backend.database.service import location_service, user_service, review_service
from backend.routers.users import ApiUser
import backend.util.errors as errors
from backend.util.types import LatitudeCoordinate, LongitudeCoordinate

router = APIRouter(
    prefix = "/locations",
    tags = ["locations"]
)

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
    except errors.UserDoesNotExist:
        raise HTTPException(400, "User does not exist!")
    except errors.UserLowTrust:
        raise HTTPException(403, "User not trusted enough!")

    detailed = LocationDetailed(**info.dict(), recent_reviews=[], trust_score=trust_score)
    new_id = await location_service.insert(detailed, adding_user.id)
    return { "id": new_id }

@router.put("/{location_id}")
async def update_location(user: ApiUser, location_info: LocationHistoryIn):
    try:
        await location_service.update(user, location_info)
    except Exception as e:
        print(e)
        raise HTTPException(400, f"Some error occured! {type(e)}, {e}")

    return { "message": "success" }

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
async def get_reviews(location_id: PydanticObjectId, offset: int = 0, n: int = 10) -> ReviewsPage:
    """
        Get `n` reviews starting from the `offset`th entry.
    """

    reviews, new_offset = await review_service.get_page(location_id, offset, n)

    reviews = [ReviewOut(**r.dict()) for r in reviews]

    return ReviewsPage(reviews=reviews, next_offset=new_offset)

@review_router.post("/")
async def create_review(user: ApiUser, review: ReviewInfo):
    # error if location not found
    loc = await location_service.get(review.location_id)
    if not loc:
        raise HTTPException(404, "Location not found!")

    try:
        review_id = await review_service.create(user, review)
    except errors.UserHasReviewAlready:
        raise HTTPException(400, "User already has a review for that location!")

    return review_id

@review_router.put("/")
async def update_review(user: ApiUser, review_id: PydanticObjectId, review: ReviewInfo):
    try:
        await review_service.update(user, review_id, review)
    except errors.ReviewDoesNotExist:
        raise HTTPException(404, "Review with given id not found!")
    except errors.UserDoesNotOwnReview:
        raise HTTPException(401, "Not authorized to update this review!")

    return { "message": "success" }

@review_router.delete("/")
async def remove_review(user: ApiUser, review_id: PydanticObjectId):
    try:
        await review_service.delete(user, review_id)
    except errors.ReviewDoesNotExist:
        raise HTTPException(404, "Review with given id not found!")
    except errors.UserDoesNotOwnReview:
        raise HTTPException(401, "Not authorized to delete this review!")

    return { "message": "success" }

@review_router.put("/{review_id}")
async def report_review(user: ApiUser, review_id: PydanticObjectId, reason: str):
    try:
        await review_service.report(user, review_id, reason)
    except errors.UserHasAlreadyReportedThisReview:
        raise HTTPException(401, "User has already reported this review!")

    return { "message": "success" }

@review_router.put("/confirmation")
async def set_confirmation(user: ApiUser, location_id: PydanticObjectId, confirm: bool = True):
    # TODO: functionality has to be implemented
    # await review_service.confirm_location(user, location_id, confirm)
    raise NotImplementedError()

router.include_router(review_router)
