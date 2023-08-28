import enum
from datetime import date
from enum import Enum
from typing import Annotated, Literal, Union

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from pymongo import DESCENDING, GEO2D, GEOSPHERE, IndexModel

from backend.util.types import Datetime, TimeSlotFixed, TimeSlotFlexible

from .shared import DescriptionWithTitle, GeoJsonLocation, UserBase


class OfferType(str, Enum):
    SINGLE = "single"
    FLEXIBLE = "flexible"

    # TODO: implement recurring dates
    # BUT: search logic gets more difficult with this one...
    # RECURRING = "recurring"


class OfferVisibility(str, Enum):
    PUBLIC = "public"
    # DRAFT = "draft"
    # FRIENDS = "friends"
    # FOLLOWERS = "followers"


class OfferStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    TIMEOUT = "timeout"
    # DELETED = "deleted"
    # ARCHIVED = "archived"


class OfferLocationBase(BaseModel):
    coords: GeoJsonLocation | None


class OfferLocationArea(OfferLocationBase):
    # type: Literal["area"] = "area"
    coords: GeoJsonLocation

    # @validator("coords")
    # def prevent_empty(cls, v):
    #     assert v is not None, "Coordinates must be given"
    #     return v


class OfferLocationConnected(OfferLocationBase):
    # type: Literal["location"] = "location"
    id: PydanticObjectId


OfferLocation = Annotated[
    Union[OfferLocationConnected, OfferLocationArea], Field()  # discriminator="type")
]


class Recurrence(BaseModel):
    weekdays: int  # encoded as binary number, 255 combinations of weekdays
    until: date


TimeSlot = TimeSlotFlexible | TimeSlotFixed


class OfferTimeFlexible(BaseModel):
    # Literal annotation needed parser discriminator
    type: Literal[OfferType.FLEXIBLE] = OfferType.FLEXIBLE


class OfferTimeSingle(BaseModel):
    type: Literal[OfferType.SINGLE] = OfferType.SINGLE
    times: TimeSlotFixed


# class OfferTimeRecurring(BaseModel):
#

# TODO: write a validator for different OfferTime modes
OfferTime = Annotated[
    Union[OfferTimeFlexible, OfferTimeSingle], Field(discriminator="type")
]


# class OfferTime(BaseModel):
#     """
#     `type` determines the general sentiment of the offer.
#     `times` describes daytimes on which the offer is active. If empty or None,
#         the time is flexible during the day.
#     `recurrence` describes weekdays on which the offer is recurring for the
#         given times (above). Also, an `until` date can be given to stop the offer.
#
#     Possible combinations:
#     1. case (totally free):
#         type: FLEXIBLE
#         times: None
#         # recurrence: None
#     2. case (one fixed day with times):
#         type: SINGLE
#         times: [2023-12-30:18-00-00, 2023-12-30:19-00-00]
#         # recurrence:
#         #     weekdays: [1,2,3]
#         #     until: 2023-12-30
#     """
#
#     type: OfferType
#     times: TimeSlotFixed | list[TimeSlot] | None = None
#     # recurrence: Recurrence | None


class ParticipantStatus(str, Enum):
    HOST = "host"
    REQUESTED = "requested"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    WITHDRAWN = "withdrawn"


class Participant(BaseModel):
    id: PydanticObjectId
    status: ParticipantStatus


class LocationBlurrBase(BaseModel):
    radius: float  # in km


class LocationBlurrIn(LocationBlurrBase):
    ...


class LocationBlurrOut(LocationBlurrBase):
    center: GeoJsonLocation


class OfferCreatorInfo(UserBase):
    id: PydanticObjectId


class OfferBase(BaseModel):
    activity: list[str]
    time: OfferTime
    description: DescriptionWithTitle
    visibility: OfferVisibility
    visibility_radius: float  # in km
    location: OfferLocation
    participant_limits: list[int]


class OfferIn(OfferBase):
    blurr: LocationBlurrIn


class OfferWithParticipants(OfferBase):
    participants: list[Participant]


class OfferOut(OfferWithParticipants):
    id: PydanticObjectId
    user_info: OfferCreatorInfo
    location: OfferLocation | None
    blurr_info: LocationBlurrOut


class Offer(Document, OfferWithParticipants):
    user_info: OfferCreatorInfo
    creation_date: Datetime
    status: OfferStatus
    blurr_info: LocationBlurrOut

    class Settings:
        name = "offers"
        indexes = [
            IndexModel([("activity", DESCENDING)], name="activity_index_DESC"),
            # IndexModel(
            #     [("location.coords.coordinates", GEO2D)], name="location_index_GEO2D"
            # ),
            # Needed for Near find operator
            IndexModel([("location.coords", GEOSPHERE)], name="location_index_GEO"),
            IndexModel(
                [("blurr_info.center", GEOSPHERE)], name="blurr_location_index_GEO"
            ),
        ]
