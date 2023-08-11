from datetime import datetime
from enum import Enum

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, IPvAnyAddress
from pymongo import GEOSPHERE, IndexModel

from backend.database.models.shared import GeoJsonLocation, PhotoInfo, UserBase
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


class UserWithoutId(UserBase):
    trust_score: int
    avatar: PhotoInfo | None
    ip_address: IPvAnyAddress | None = None
    creation_date: Datetime
    last_location: GeoJsonLocation | None = None
    authentication: Authentication
    archived_until: Datetime | None = None
    admin: bool | None = None


class User(Document, UserWithoutId):
    id: PydanticObjectId

    class Settings:
        name = "users"
        indexes = [
            "username",
            "trust_score",
            IndexModel([("last_location", GEOSPHERE)], name="last_location_index_GEO"),
        ]


class NewUser(Document, UserWithoutId):
    id: PydanticObjectId | None = None
    verification_code: str | None = None

    class Settings:
        name = "users"


class VerifyUserInfo(BaseModel):
    id: PydanticObjectId
    verification_code: str


class UserApiOut(UserBase):
    id: PydanticObjectId
    avatar: PhotoInfo | None


class UserApiIn(UserBase):
    email: str
    password: str


class UserDetailed(UserWithoutId):
    id: PydanticObjectId


class UserPasswordReset(Document):
    username: str
    expiry: Datetime
    token: str
    ip_address: IPvAnyAddress | None

    class Settings:
        name = "password_reset_requests"
        indexes = ["username"]


class RelationStatus(str, Enum):
    ACCEPTED = "accepted"
    PENDING = "pending"
    DECLINED = "declined"
    CHATTING = "chatting"


class UserRelation(Document):
    users: list[PydanticObjectId]
    creation_date: Datetime
    status: RelationStatus

    class Settings:
        name = "user_relations"


class MessageType(str, Enum):
    PLAIN = "plain"
    OFFER_REACTION = "offer_reaction"
    # ANSWER = "answer"


class MessageBase(BaseModel):
    sender: PydanticObjectId
    time: datetime
    text: str
    # edited: bool


class PlainMessage(MessageBase):
    ...


class OfferReactionMessage(MessageBase):
    offer_id: PydanticObjectId


Message = OfferReactionMessage | PlainMessage


class Chat(Document):
    id: PydanticObjectId
    users: list[PydanticObjectId]
    messages: list[Message]

    class Settings:
        name = "chats"


class MessageOut(BaseModel):
    chat_id: PydanticObjectId
    message: Message
