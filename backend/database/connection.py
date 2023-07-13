import os

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from backend.database.models.locations import (
    LocationDetailedDB,
    LocationHistory,
    LocationShortDB,
    LocationUpdateReport,
    Review,
)
from backend.database.models.offers import Offer
from backend.database.models.users import (
    Chat,
    NewUser,
    User,
    UserPasswordReset,
    UserRelation,
)

client = AsyncIOMotorClient(os.getenv("MONGODB_CONNECTION_STRING"))


async def init():
    documents = [
        UserPasswordReset,
        UserRelation,
        LocationDetailedDB,
        LocationShortDB,
        Review,
        LocationHistory,
        Offer,
        LocationUpdateReport,
        Chat,
    ]

    for d in documents:
        await init_beanie(database=client.AR, document_models=[d])

    await init_beanie(database=client.AR, document_models=[NewUser, User])
