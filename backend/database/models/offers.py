from enum import Enum
from uuid import UUID

from beanie import Document
from pydantic import BaseModel
from pymongo import DESCENDING, GEOSPHERE, IndexModel

from ...util.types import Datetime, TimeSlotFixed, TimeSlotFlexible
from .shared import GeoJSONLocation, UserBase


class OfferType(str, Enum):
    SINGLE = "single"
    RECURRING = "recurring"
    FLEXIBLE = "flexible"


class OfferVisibility(str, Enum):
    FRIENDS = "friends"
    PUBLIC = "public"
    FOLLOWERS = "followers"
    DRAFT = "draft"


class OfferStatus(str, Enum):
    OPEN = "open"
    DELETED = "deleted"
    CLOSED = "closed"
    ARCHIVED = "archived"


class OfferLocation(BaseModel):
    center: GeoJSONLocation
    location_id: UUID | None
    radius: float | None


class Recurrence(BaseModel):
    weekdays: int  # encoded as binary number, 255 combinations of weekdays
    from_to: TimeSlotFlexible


class OfferTime(BaseModel):
    type: OfferType
    times: list[TimeSlotFlexible | TimeSlotFixed] | None
    recurrence: Recurrence | None


class Offer(Document):
    user_info: UserBase
    activity: list[str]
    location: OfferLocation
    time: OfferTime
    description: str
    creation_date: Datetime
    visibility: OfferVisibility
    status: OfferStatus

    class Settings:
        name = "offers"
        indexes = [
            IndexModel([("activity", DESCENDING)], name="activity_index_DESC"),
            IndexModel([("location", GEOSPHERE)], name="location_index_GEO"),
            # IndexModel([("time", DESCENDING)], name="time_index_DESC"),
            # IndexModel([("activity", DESCENDING)], name="activity_index_DESC"),
        ]
