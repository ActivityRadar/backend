from datetime import datetime
from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel

import backend.util.errors as errors
from backend.database.models.locations import (
    LocationDetailed,
    LocationDetailedApi,
    LocationHistoryIn,
    LocationNew,
    LocationShortApi,
    LocationShortDb,
    ReviewBase,
    ReviewsPage,
    ReviewsSummary,
    ReviewWithId,
)
from backend.database.models.shared import PhotoInfo, PhotoUrl
from backend.database.service import location_service, review_service, user_service
from backend.routers.users import ApiUser
from backend.util.types import LatitudeCoordinate, LongitudeCoordinate

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("/bbox")
async def get_locations_by_bbox(
    west: LongitudeCoordinate,
    south: LatitudeCoordinate,
    east: LongitudeCoordinate,
    north: LatitudeCoordinate,
    activities: list[str] | None = Query(None),
) -> list[LocationShortApi]:
    bbox = ((west, south), (east, north))
    short: list[LocationShortDb] = await location_service.get_bbox_short(
        bbox, activities
    )
    result: list[LocationShortApi] = [LocationShortApi(**loc.dict()) for loc in short]
    return result


@router.get("/around")
async def get_locations_around(
    long: LongitudeCoordinate,
    lat: LatitudeCoordinate,
    radius: Annotated[float | None, "Distance in km"] = Query(None),
    activities: list[str] | None = Query(None),
    limit: int = Query(default=20, description="Closest n locations to be returned"),
) -> list[LocationDetailedApi]:
    center = (long, lat)
    short = await location_service.get_around(
        center=center, radius=radius, activities=activities, limit=limit
    )
    result: list[LocationDetailedApi] = [
        LocationDetailedApi(**loc.dict()) for loc in short
    ]
    return result


@router.get("/{location_id}")
async def get_location(location_id: PydanticObjectId) -> LocationDetailedApi:
    result = await location_service.get(location_id)
    if result is None:
        raise HTTPException(404, detail=f"No location with {location_id=} exists!")
    return LocationDetailedApi(**result.dict())


@router.get("/bulk")
async def get_location_bulk(location_ids: list[PydanticObjectId] = Query(alias="id")):
    ids = list(set(location_ids))  # remove duplicates
    locations = []
    for id in ids:
        loc = await location_service.get(id)
        if loc:
            locations.append(loc)

    return [LocationDetailedApi(**loc.dict()) for loc in locations]


class CreateLocationResponse(BaseModel):
    id: PydanticObjectId


@router.post("/")
async def create_new_location(
    adding_user: ApiUser, info: LocationNew
) -> CreateLocationResponse:
    try:
        trust_score = await user_service.check_eligible_to_add(adding_user.id)
    except errors.UserDoesNotExist:
        raise HTTPException(400, "User does not exist!")
    except errors.UserLowTrust:
        raise HTTPException(403, "User not trusted enough!")

    detailed = LocationDetailed(
        **info.dict(),
        reviews=ReviewsSummary(count=0, average_rating=0, recent=[]),
        trust_score=trust_score,
        photos=[],
    )
    new_id = await location_service.insert(detailed, adding_user.id)

    return CreateLocationResponse(id=new_id)


@router.put("/")
async def update_location(user: ApiUser, location_info: LocationHistoryIn):
    try:
        await location_service.update(user, location_info)
    except Exception as e:
        print(e)
        raise HTTPException(400, f"Some error occured! {type(e)}, {e}")


@router.get("/{location_id}/update-history")
async def get_location_history(location_id: PydanticObjectId, offset: int = 0):
    history = await location_service.get_history(location_id, offset)
    return history


@router.post("/report-update/{update_id}")
async def report_location_update(
    user: ApiUser, update_id: PydanticObjectId, reason: str
):
    try:
        report_id = await location_service.report_update(user, update_id, reason)
    except:
        raise HTTPException(500, "Something went wrong!")
    return {"message": "success", "report_id": report_id}


@router.delete("/{location_id}")
def delete_location(location_id: int):
    # error if location not found

    # error if user has no rights to remove location

    pass


#### REVIEWS

review_router = APIRouter(prefix="/{location_id}/reviews", tags=["reviews"])


@review_router.get("/")
async def get_reviews(
    location_id: PydanticObjectId, offset: int = 0, n: int = 10
) -> ReviewsPage:
    """
    Get `n` reviews starting from the `offset`th entry.
    """

    reviews, new_offset = await review_service.get_page(location_id, offset, n)

    reviews = [ReviewWithId(**r.dict()) for r in reviews]

    return ReviewsPage(reviews=reviews, next_offset=new_offset)


@review_router.post("/")
async def create_review(
    user: ApiUser, location_id: PydanticObjectId, review: ReviewBase
):
    # error if location not found
    loc = await location_service.get(location_id)
    if not loc:
        raise HTTPException(404, "Location not found!")

    try:
        review_id = await review_service.create(user, review)
    except errors.UserHasReviewAlready:
        raise HTTPException(400, "User already has a review for that location!")

    return review_id


@review_router.put("/{review_id}")
async def update_review(
    user: ApiUser,
    location_id: PydanticObjectId,
    review_id: PydanticObjectId,
    review: ReviewBase,
):
    try:
        await review_service.update(user, review_id, review)
    except errors.ReviewDoesNotExist:
        raise HTTPException(404, "Review with given id not found!")
    except errors.UserDoesNotOwnReview:
        raise HTTPException(401, "Not authorized to update this review!")


@review_router.delete("/{review_id}")
async def remove_review(
    user: ApiUser, location_id: PydanticObjectId, review_id: PydanticObjectId
):
    try:
        await review_service.delete(user, review_id)
    except errors.ReviewDoesNotExist:
        raise HTTPException(404, "Review with given id not found!")
    except errors.UserDoesNotOwnReview:
        raise HTTPException(401, "Not authorized to delete this review!")


@review_router.put("/{review_id}/report")
async def report_review(
    user: ApiUser,
    location_id: PydanticObjectId,
    review_id: PydanticObjectId,
    reason: str,
):
    try:
        await review_service.report(user, review_id, reason)
    except errors.UserHasAlreadyReportedThisReview:
        raise HTTPException(401, "User has already reported this review!")


@review_router.put("/confirmation")
async def set_confirmation(
    user: ApiUser, location_id: PydanticObjectId, confirm: bool = True
):
    # TODO: functionality has to be implemented
    # await review_service.confirm_location(user, location_id, confirm)
    raise NotImplementedError()


photo_router = APIRouter(prefix="/{location_id}/photos", tags=["photos"])


@photo_router.post("/")
async def add_photo(user: ApiUser, location_id: PydanticObjectId, photo_url: PhotoUrl):
    photo_info = PhotoInfo(
        user_id=user.id, url=photo_url.url, creation_date=datetime.utcnow()
    )

    try:
        await location_service.add_photo(
            user=user, location_id=location_id, photo=photo_info
        )
    except errors.UserPostedTooManyPhotos:
        raise HTTPException(405, "Cant post more photo for this location!")


@photo_router.delete("/")
async def remove_photo(
    user: ApiUser, location_id: PydanticObjectId, photo_url: PhotoUrl
):
    owner = await location_service.get_photo_owner(location_id, photo_url.url)

    if user.id != owner:
        raise HTTPException(405, "User does not own photo!")

    await location_service.remove_photo(location_id, photo_url.url)


@photo_router.put("/report")
async def report_photo(
    user: ApiUser, location_id: PydanticObjectId, photo_url: PhotoUrl
):
    # TODO: implement
    pass


router.include_router(review_router)
router.include_router(photo_router)
