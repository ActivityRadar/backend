from datetime import datetime
from enum import Enum
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import BaseModel
from pymongo import GEO2D, GEOSPHERE, IndexModel

from backend.database.models.shared import (
    CreationInfo,
    DescriptionWithTitle,
    GeoJsonLocation,
    GeoJsonObject,
    PhotoInfo,
)
from backend.util.types import Datetime


class ReviewBase(BaseModel):
    location_id: PydanticObjectId
    description: DescriptionWithTitle
    overall_rating: float
    details: dict[str, Any]


class ReviewApiIn(ReviewBase):
    ...


class ReviewInfo(ReviewBase):
    creation_date: Datetime
    user_id: PydanticObjectId


class ReviewWithId(ReviewInfo):
    id: PydanticObjectId


class Review(Document, ReviewInfo):
    class Settings:
        name = "reviews"


class ReviewsSummary(BaseModel):
    average_rating: float
    count: int
    recent: list[ReviewWithId]


class LocationBase(BaseModel):
    activity_types: list[str]
    location: GeoJsonLocation
    name: str | None
    trust_score: int


class LocationShort(LocationBase):
    average_rating: float


class LocationDetailed(LocationBase):
    tags: dict[str, Any]
    geometry: GeoJsonObject | None
    photos: list[PhotoInfo]
    reviews: ReviewsSummary


class LocationDetailedDb(Document, LocationDetailed):
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


class LocationShortDb(Document, LocationShort):
    class Settings:
        name = "simple_locations"
        indexes = [
            "activity_type",
            IndexModel([("location.coordinates", GEO2D)], name="location_index_GEO2D"),
            IndexModel([("location", GEOSPHERE)], name="location_index_GEOSPHERE"),
        ]


class LocationNew(LocationBase):
    name: str | None = None
    tags: dict[str, Any] = {}
    geometry: GeoJsonObject | None = None


class LocationShortApi(LocationBase):
    id: PydanticObjectId


class LocationDetailedApi(LocationDetailed):
    id: PydanticObjectId


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


class LocationHistory(Document, LocationHistoryIn):
    user_id: PydanticObjectId
    date: Datetime

    class Settings:
        name = "location_change_history"


class ReviewsPage(BaseModel):
    next_offset: int | None
    reviews: list[ReviewWithId]


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
