from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from .models.locations import LocationDetailed, LocationHistory, LocationShort
from .models.offers import Offer
from .models.shared import Review
from .models.users import User

client = AsyncIOMotorClient("mongodb://user:pass@host:27017")

async def init():
    await init_beanie(database=client.AR, document_models=[User])
    await init_beanie(database=client.AR, document_models=[LocationDetailed])
    await init_beanie(database=client.AR, document_models=[LocationShort])
    await init_beanie(database=client.AR, document_models=[Review])
    await init_beanie(database=client.AR, document_models=[LocationHistory])
    await init_beanie(database=client.AR, document_models=[Offer])
