from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from backend.database.models.locations import (
    LocationDetailedDb,
    LocationHistory,
    LocationShortDb,
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
from backend.util import constants

client = AsyncIOMotorClient(constants.MONGODB_CONNECTION_STRING)


async def init():
    documents = [
        UserPasswordReset,
        UserRelation,
        LocationDetailedDb,
        LocationShortDb,
        Review,
        LocationHistory,
        Offer,
        LocationUpdateReport,
        Chat,
    ]

    for d in documents:
        print(f"init {d}")
        await init_beanie(database=client[constants.DATABASE_NAME], document_models=[d])

    await init_beanie(
        database=client[constants.DATABASE_NAME], document_models=[NewUser, User]
    )
