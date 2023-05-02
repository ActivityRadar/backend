from datetime import datetime
from typing import Any, Optional

from beanie import Document
from pydantic import IPvAnyAddress
from pymongo import GEOSPHERE, IndexModel

from .shared import BasicUserInfo, GeoJSONLocation

class User(Document, BasicUserInfo):
    trust_score: int
    ip_address: Optional[IPvAnyAddress]
    creation_date: datetime
    last_location: Optional[GeoJSONLocation]
    authentication: Any

    """
        "authentication": {
            "description": "User authentication information.",
            "bsonType": "object",
            "properties": {
                "type": {
                    "description": "Authentication type",
                    "bsonType": "string",
                    "pattern": "(apple|google|email)"
                },
                "email": {
                    "description": "User's email address.",
                    "bsonType": "string"
                },
                "passwordHash": {
                    "description": "User password hash.",
                    "bsonType": "string"
                }
            },
    """

    class Settings:
        name = "users"
        indexes = [
            "username",
            "trust_score",
            IndexModel([("last_location", GEOSPHERE)],
                       name="last_location_index_GEO")
        ]
