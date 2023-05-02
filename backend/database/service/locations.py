from beanie import PydanticObjectId
from backend.database.models.locations import LocationDetailed, LocationShort

class LocationService:
    def __init__(self) -> None:
        # take care, the ODM classes might not have been initialized by beanie yet...
        # print(dir(LocationDetailed.find_all()))
        return

    def insert(self, location: LocationDetailed):
        self.check_possible_duplicate(location)

    async def get(self, id: PydanticObjectId) -> LocationDetailed | None:
        return await LocationDetailed.get(id)

    def get_bbox_short(self, bbox) -> list[LocationShort]:
        pass

    def check_possible_duplicate(self, location: LocationDetailed) -> None | list[LocationDetailed]:
        return None



