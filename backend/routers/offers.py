from datetime import datetime, timedelta

from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, Query

from backend.database.models.offers import (
    OfferIn,
    OfferStatus,
    OfferTimeFlexible,
    OfferTimeSingle,
)
from backend.database.service import (
    offer_service,
    relation_service,
    user_service,
)
from backend.routers.users import ApiUser
from backend.util import errors
from backend.util.types import LatitudeCoordinate, LongitudeCoordinate

router = APIRouter(prefix="/offers", tags=["offers"])


def create_search_time(time_from: datetime | None, time_until: datetime | None):
    if time_from is None and time_until is None:
        return OfferTimeFlexible()

    if time_from is None:
        time_from = time_from or datetime.utcnow()
    else:
        # allow to look back some time amount
        now = datetime.utcnow() - timedelta(hours=2)
        if time_from < now:
            raise HTTPException(401, "Invalid `from` time!")

    if time_until is None:
        # look forward a day by default
        # TODO: extract the hardcoded +1 day to a constant
        time_until = datetime.utcnow() + timedelta(days=1)
    else:
        if time_until < time_from:
            raise HTTPException(401, "Invalid `until` time!")

    return OfferTimeSingle(times=(time_from, time_until))


@router.post("/")
async def create_offer(user: ApiUser, offer_info: OfferIn):
    try:
        id = await offer_service.create(user, offer_info)
    except errors.LocationDoesNotExist:
        raise HTTPException(404, "Location not found!")

    return {"message": "success", "offer_id": id}


@router.get("/")
async def get_offers(user: ApiUser, id: list[PydanticObjectId] = Query()):
    ids = list(set(id))  # remove duplicates

    offers = offer_service.get(ids)

    return offers


@router.get("/location/{location_id}")
async def get_offers_at_location(
    user: ApiUser,
    location_id: PydanticObjectId,
    time_from: datetime = Query(None),
    time_until: datetime = Query(None),
):
    search_time = create_search_time(time_from, time_until)

    try:
        offers = await offer_service.get_at_location(user, location_id, search_time)
    except errors.LocationDoesNotExist:
        raise HTTPException(404, "Location not found!")

    return offers


@router.get("/around")
async def get_offers_in_area(
    user: ApiUser,
    long: LongitudeCoordinate,
    lat: LatitudeCoordinate,
    radius: float,
    time_from: datetime = Query(None),
    time_until: datetime = Query(None),
    activities: list[str] = Query(None),
):
    search_time = create_search_time(time_from, time_until)
    return await offer_service.get_around(
        user, (long, lat), radius, search_time, activities
    )


@router.put("/{offer_id}")
async def contact_offerer(user: ApiUser, offer_id: PydanticObjectId, message: str):
    try:
        offer = (await offer_service.get([offer_id]))[0]
    except IndexError:
        raise HTTPException(404, "Offer not found!")

    offerer = await user_service.get_by_id(offer.user_info.id)
    if not offerer:
        # should not happen
        raise HTTPException(404, "Offerer does not exist (anymore)!")

    user_ids = [user.id, offer.user_info.id]
    relation = await relation_service.has_relation_to(user.id, offerer.id)
    if not relation:
        relation = await relation_service.create_chatting(user_ids)




def ignore_offers_from_user():
    pass


def unignore_offers_from_user():
    pass


def decline_reaction():
    pass


def accept_reaction():
    pass
