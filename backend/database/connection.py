import os

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from .models.locations import LocationDetailedDB, LocationHistory, LocationShortDB
from .models.offers import Offer
from .models.shared import Review
from .models.users import User

client = AsyncIOMotorClient(os.getenv("MONGODB_CONNECTION_STIRNG"))

async def init():
    await init_beanie(database=client.AR, document_models=[User])
    await init_beanie(database=client.AR, document_models=[LocationDetailedDB])
    await init_beanie(database=client.AR, document_models=[LocationShortDB])
    await init_beanie(database=client.AR, document_models=[Review])
    await init_beanie(database=client.AR, document_models=[LocationHistory])
    await init_beanie(database=client.AR, document_models=[Offer])
