from enum import Enum
from typing import Any

from beanie import PydanticObjectId
from pydantic import BaseModel

from backend.util.types import Datetime

LongLat = list[float]


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


class PhotoUrl(BaseModel):
    url: str


class GeoJsonLocation(BaseModel):
    type: str = "Point"
    coordinates: LongLat


class GeoJsonLine(BaseModel):
    type: str = "LineString"
    coordinates: list[LongLat]


class GeoJsonFeatureCollection(BaseModel):
    type: str = "GeometryCollection"
    geometries: list[dict[str, Any]]


GeoJsonObject = GeoJsonLocation | GeoJsonLine | GeoJsonFeatureCollection


class UserBase(BaseModel):
    username: str
    display_name: str
