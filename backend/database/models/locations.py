from datetime import datetime
from enum import Enum
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import BaseModel
from pymongo import GEO2D, GEOSPHERE, IndexModel

from backend.database.models.shared import (
    CreationInfo,
    GeoJSONLocation,
    GeoJSONObject,
    PhotoInfo,
)
from backend.util.types import Datetime


class ReviewInfo(BaseModel):
    location_id: PydanticObjectId
    text: str  # TODO limit in length
    overall_rating: float
    details: dict[str, Any]


class ReviewBase(ReviewInfo):
    creation_date: Datetime
    user_id: PydanticObjectId


class LocationBase(BaseModel):
    activity_type: str
    location: GeoJSONLocation


class LocationShort(LocationBase):
    name: str | None
    trust_score: int
    average_rating: float | None


class LocationDetailed(LocationShort):
    tags: dict[str, Any]
    recent_reviews: list[ReviewBase]
    geometry: GeoJSONObject | None
    photos: list[PhotoInfo] | None


class LocationDetailedDB(Document, LocationDetailed):
    creation: CreationInfo
    last_modified: datetime
    osm_id: int | None = None

    class Settings:
        name = "locations"
        indexes = [
            "osm_id",
            "activity_type",
            # for Box queries
            IndexModel([("location.coordinates", GEO2D)], name="location_index_GEO2D"),
            # for Near queries
            IndexModel([("location", GEOSPHERE)], name="location_index_GEOSPHERE"),
        ]


class LocationShortDB(Document, LocationShort):
    class Settings:
        name = "simple_locations"
        indexes = [
            "activity_type",
            IndexModel([("location.coordinates", GEO2D)], name="location_index_GEO2D"),
            IndexModel([("location", GEOSPHERE)], name="location_index_GEOSPHERE"),
        ]


class LocationNew(LocationBase):
    name: str | None = None
    photos: list[PhotoInfo] = []
    tags: dict[str, Any] = {}
    geometry: GeoJSONObject | None = None


class LocationShortAPI(LocationBase):
    id: PydanticObjectId


class LocationDetailedAPI(LocationDetailed):
    ...


class TagChangeType(str, Enum):
    ADD = "add"
    DELETE = "delete"
    CHANGE = "change"


TagContent = str


class TagChange(BaseModel):
    mode: TagChangeType
    content: TagContent | list[TagContent]  # Any for Add and delete, tuple for changes


class LocationHistoryIn(BaseModel):
    location_id: PydanticObjectId
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    tags: dict[str, TagChange] | None


class LocationHistory(LocationHistoryIn, Document):
    user_id: PydanticObjectId
    date: Datetime

    class Settings:
        name = "location_change_history"


class Review(ReviewBase, Document):
    class Settings:
        name = "reviews"


class ReviewIn(ReviewInfo):
    ...


class ReviewOut(Review):
    id: PydanticObjectId


class ReviewsPage(BaseModel):
    next_offset: int | None
    reviews: list[ReviewOut]


class ReviewReport(Document):
    review_id: PydanticObjectId
    user_id: PydanticObjectId
    reason: str
    report_date: Datetime

    class Settings:
        name = "review_reports"


class LocationUpdateReport(Document):
    user_id: PydanticObjectId
    update_id: PydanticObjectId
    reason: str
    date: Datetime

    class Settings:
        name = "location_update_reports"
