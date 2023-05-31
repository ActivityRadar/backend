from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import BaseModel
from pymongo import GEOSPHERE, IndexModel

from backend.database.models.shared import (
    CreationInfo,
    GeoJSONLocation,
    GeoJSONObject,
    PhotoInfo,
)
from backend.util.types import Datetime

class ReviewInfo(BaseModel):
    location_id: PydanticObjectId
    text: str # TODO limit in length
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
            IndexModel([("location", GEOSPHERE)],
                       name="location_index_GEO")
        ]

class LocationShortDB(Document, LocationShort):
    class Settings:
        name = "simple_locations"
        indexes = [
            "activity_type",
            IndexModel([("location", GEOSPHERE)],
                       name="location_index_GEO")
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

class LocationHistory(Document):
    pass

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
