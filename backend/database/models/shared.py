from enum import Enum
from typing import Any
from uuid import UUID

from beanie import Document, PydanticObjectId
from pydantic import BaseModel

from backend.util.types import Datetime, LongLat

class LocationCreators(Enum):
    OSM = "OSM"
    APP = "APP"

class CreationInfo(BaseModel):
    created_by: LocationCreators
    date: Datetime
    user_id: PydanticObjectId | None

class PhotoInfo(BaseModel):
    user_id: PydanticObjectId
    url: str
    creation_date: Datetime

class Review(Document):
    user_id: UUID
    text: str
    creation_date: Datetime
    overall_rating: float
    details: dict[str, Any]

class GeoJSONLocation(BaseModel):
    type: str = "Point"
    coordinates: list[float]

class GeoJSONLine(BaseModel):
    type: str = "LineString"
    coordinates: list[LongLat]

class GeoJSONFeatureCollection(BaseModel):
    type: str = "GeometryCollection"
    geometries: list[dict[str, Any]]

GeoJSONObject = GeoJSONLocation | GeoJSONLine | GeoJSONFeatureCollection

class UserBase(BaseModel):
    username: str
    display_name: str
    avatar: PhotoInfo | None

