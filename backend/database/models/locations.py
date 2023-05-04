from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import BaseModel
from pymongo import IndexModel, GEOSPHERE

from .shared import CreationInfo, GeoJSONLocation, GeoJSONObject, PhotoInfo, Review

class LocationBase(BaseModel):
    activity_type: str
    location: GeoJSONLocation

class LocationShort(LocationBase):
    name: str | None
    trust_score: int

class LocationDetailed(LocationShort):
    tags: dict[str, Any]
    recent_reviews: list[Review]
    geometry: GeoJSONObject | None
    photos: list[PhotoInfo] | None

class LocationDetailedDB(Document, LocationDetailed):
    osm_id: int
    creation: CreationInfo
    last_modified: datetime

    class Settings:
        name = "locations"
        indexes = [
            "osm_id",
            "activity_type",
            IndexModel([("location", GEOSPHERE)],
                       name="location_index_GEO")
        ]

class LocationShortDB(Document, LocationShort):
    detailed: PydanticObjectId

    class Settings:
        name = "simple_locations"
        indexes = [
            "activity_type",
            IndexModel([("location", GEOSPHERE)],
                       name="location_index_GEO")
        ]

class LocationShortAPI(LocationBase):
    ...

class LocationDetailedAPI(LocationDetailed):
    ...

class LocationHistory(Document):
    pass

