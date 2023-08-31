from datetime import datetime, timedelta

from beanie import PydanticObjectId
from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel

from backend.database.models.offers import (
    Offer,
    OfferIn,
    OfferOut,
    OfferStatus,
    OfferTimeFlexible,
    OfferTimeSingle,
)
from backend.database.service import (
    chat_service,
    offer_service,
    relation_service,
    user_service,
)
from backend.routers.auth import ApiUser
from backend.util import errors
from backend.util.types import LatitudeCoordinate, LongitudeCoordinate

router = APIRouter(prefix="/offers", tags=["offers"])


class CreateOfferResponse(BaseModel):
    offer_id: PydanticObjectId


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


def to_offer_out(offer):
    return OfferOut(**offer.dict())


def include_location_for_host(offers: list[Offer], user_id: PydanticObjectId):
    res = []
    for offer in offers:
        out = to_offer_out(offer)
        if out.user_info.id != user_id:
            out.location = None

        res.append(out)

    return res


@router.post("/")
async def create_offer(user: ApiUser, offer_info: OfferIn) -> OfferOut:
    try:
        offer = await offer_service.create(user, offer_info)
    except errors.LocationDoesNotExist:
        raise HTTPException(404, "Location not found!")

    return to_offer_out(offer)


@router.get("/")
async def get_offers(
    user: ApiUser,
    offer_ids: list[PydanticObjectId] | None = Query(None, alias="id"),
    all: bool = Query(False, alias="all-for-user"),
) -> list[OfferOut]:
    if all:
        offers = await offer_service.get_for_user(user)
    else:
        if not offer_ids:
            raise HTTPException(
                403, "Either `all-for-user` must be true, or `id`s given!"
            )

        ids = list(set(offer_ids))  # remove duplicates
        offers = await offer_service.get_bulk(ids)

    return include_location_for_host(offers, user.id)


@router.get("/location/{location_id}")
async def get_offers_at_location(
    user: ApiUser,
    location_id: PydanticObjectId,
    time_from: datetime = Query(None),
    time_until: datetime = Query(None),
) -> list[OfferOut]:
    search_time = create_search_time(time_from, time_until)

    try:
        offers = await offer_service.get_at_location(user, location_id, search_time)
    except errors.LocationDoesNotExist:
        raise HTTPException(404, "Location not found!")

    return include_location_for_host(offers, user.id)


@router.get("/around")
async def get_offers_in_area(
    user: ApiUser,
    long: LongitudeCoordinate,
    lat: LatitudeCoordinate,
    radius: float,
    time_from: datetime = Query(None),
    time_until: datetime = Query(None),
    activities: list[str] = Query(None),
) -> list[OfferOut]:
    search_time = create_search_time(time_from, time_until)
    offers = await offer_service.get_around(
        user, (long, lat), radius, search_time, activities
    )

    return include_location_for_host(offers, user.id)


@router.put("/me/{offer_id}")
async def set_offer_status(
    user: ApiUser, offer_id: PydanticObjectId, status: OfferStatus
):
    try:
        await offer_service.set_status(user, offer_id, status)
    except errors.UserDoesNotOwnOffer:
        raise HTTPException(401, "User does not own offer and cant modify it!")
    except errors.OfferDoesNotExist:
        raise HTTPException(404, "Offer does not exist!")


@router.put("/{offer_id}")
async def request_to_join(
    user: ApiUser, offer_id: PydanticObjectId, message: str = Body()
):
    await offer_service.request_to_join(user=user, offer_id=offer_id, message=message)


# @router.put("/{offer_id}")
# async def contact_offerer(
#     user: ApiUser, offer_id: PydanticObjectId, message: str = Body()
# ):
#     offer = await offer_service.get(offer_id)
#     if offer is None:
#         raise HTTPException(404, "Offer not found!")
#
#     offerer = await user_service.get_by_id(offer.user_info.id)
#     if not offerer:
#         # should not happen
#         raise HTTPException(404, "Offerer does not exist (anymore)!")
#
#     user_ids = [user.id, offer.user_info.id]
#     relation = await relation_service.has_relation_to(user.id, offerer.id)
#     if not relation:
#         relation = await relation_service.create_chatting(user_ids)
#
#     chat = await chat_service.get_or_create(relation)
#     await chat_service.react_to_offer(user, chat, offer_id, message)
#
#     return {"chat_id": chat.id}
#


@router.delete("/{offer_id}")
async def delete_offer(user: ApiUser, offer_id: PydanticObjectId):
    try:
        await offer_service.delete(user, offer_id)
    except errors.OfferDoesNotExist:
        raise HTTPException(404, "Offer does not exist!")
    except errors.UserDoesNotOwnOffer:
        raise HTTPException(401, "User does not own offer!")


def ignore_offers_from_user():
    pass


def unignore_offers_from_user():
    pass


@router.put("/me/{offer_id}/decline/{user_id}")
async def decline_request(
    user: ApiUser, offer_id: PydanticObjectId, user_id: PydanticObjectId
):
    await offer_service.decline_request(
        host=user, offer_id=offer_id, participant_id=user_id
    )


@router.put("/me/{offer_id}/accept/{user_id}")
async def accept_request(
    user: ApiUser, offer_id: PydanticObjectId, user_id: PydanticObjectId
):
    await offer_service.accept_request(
        host=user, offer_id=offer_id, participant_id=user_id
    )
