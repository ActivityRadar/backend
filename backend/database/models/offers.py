from enum import Enum
from typing import Optional
from uuid import UUID

from beanie import Document
from pydantic import BaseModel
from pymongo import DESCENDING, IndexModel, GEOSPHERE

from ...util.types import Datetime, TimeSlotFixed, TimeSlotFlexible
from .shared import BasicUserInfo, GeoJSONLocation

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
    location_id: Optional[UUID]
    radius: Optional[float]

class Recurrence(BaseModel):
    weekdays: int # encoded as binary number, 255 combinations of weekdays
    from_to: TimeSlotFlexible

class OfferTime(BaseModel):
    type: OfferType
    times: Optional[list[TimeSlotFlexible | TimeSlotFixed]]
    recurrence: Optional[Recurrence]

class Offer(Document):
    user_info: BasicUserInfo
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
