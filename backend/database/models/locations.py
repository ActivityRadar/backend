from datetime import datetime
from typing import Any, Optional
# from uuid import UUID

from beanie import Document, Link
from pydantic import BaseModel
from pymongo import IndexModel, GEOSPHERE

from .shared import CreationInfo, GeoJSONLocation, GeoJSONObject, PhotoInfo, Review

class SimpleLocationInfo(BaseModel):
    name: str | None
    trust_score: int
    activity_type: str
    location: GeoJSONLocation

class LocationDetailed(Document, SimpleLocationInfo):
    osm_id: int
    creation: CreationInfo
    last_modified: datetime
    tags: dict[str, Any]
    recent_reviews: list[Review]
    geometry: GeoJSONObject | None
    photos: list[PhotoInfo] | None

    class Settings:
        name = "locations"
        indexes = [
            "osm_id",
            "activity_type",
            IndexModel([("location", GEOSPHERE)],
                       name="location_index_GEO")
        ]

class LocationShort(Document, SimpleLocationInfo):
    detailed: Link[LocationDetailed]

    class Settings:
        name = "simple_locations"
        indexes = [
            "activity_type",
            IndexModel([("location", GEOSPHERE)],
                       name="location_index_GEO")
        ]

class LocationHistory():
    pass


