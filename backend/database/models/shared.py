from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel

from backend.util.types import LongLat

class LocationCreators(Enum):
    OSM = "OSM",
    APP = "APP"

class CreationInfo(BaseModel):
    created_by: LocationCreators
    date: datetime
    user_id: Optional[UUID]

class PhotoInfo(BaseModel):
    user_id: UUID
    url: str
    creation_date: datetime

class Review(BaseModel):
    user_id: UUID
    text: str
    creation_date: datetime
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

class BasicUserInfo(BaseModel):
    username: str
    display_name: str
    avatar: Optional[PhotoInfo]

