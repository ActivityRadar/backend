from enum import Enum

from beanie import Document
from pydantic import BaseModel, IPvAnyAddress
from pymongo import GEOSPHERE, IndexModel

from backend.database.models.shared import UserBase, GeoJSONLocation
from backend.util.types import Datetime


class AuthType(str, Enum):
    PASSWORD = "password"
    APPLE = "apple"
    GOOGLE = "google"

class Authentication(BaseModel):
    type: AuthType
    password_hash: str | None = None
    email: str | None = None
    # more optional members to follow

class User(Document, UserBase):
    trust_score: int
    ip_address: IPvAnyAddress | None = None
    creation_date: Datetime
    last_location: GeoJSONLocation | None = None
    authentication: Authentication
    archived_until: Datetime | None = None

    class Settings:
        name = "users"
        indexes = [
            "username",
            "trust_score",
            IndexModel([("last_location", GEOSPHERE)],
                       name="last_location_index_GEO")
        ]

class UserAPI(UserBase):
    ...

class UserIn(UserBase):
    email: str
    password: str

class UserPasswordReset(Document):
    username: str
    expiry: Datetime
    token: str
    ip_address: IPvAnyAddress | None

    class Settings:
        name = "password_reset_requests"
        indexes = [
            "username"
        ]

