import os

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from backend.database.models.locations import (
    LocationDetailedDB,
    LocationHistory,
    LocationShortDB,
    LocationUpdateReport,
    Review
)
from backend.database.models.offers import Offer
from backend.database.models.users import NewUser, User, UserPasswordReset, UserRelation

client = AsyncIOMotorClient(os.getenv("MONGODB_CONNECTION_STIRNG"))

async def init():
    documents = [UserPasswordReset, UserRelation,
                 LocationDetailedDB, LocationShortDB,
                 Review, LocationHistory, Offer, LocationUpdateReport]

    for d in documents:
        await init_beanie(database=client.AR, document_models=[d])

    await init_beanie(database=client.AR, document_models=[NewUser, User])
