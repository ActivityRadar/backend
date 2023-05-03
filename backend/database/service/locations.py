from beanie import PydanticObjectId
from beanie.operators import Box, In

from backend.database.models.locations import LocationDetailedDB, LocationShortDB
from backend.util.types import BoundingBox

class LocationService:
    def __init__(self) -> None:
        # take care, the ODM classes might not have been initialized by beanie yet...
        # print(dir(LocationDetailed.find_all()))
        return

    def insert(self, location: LocationDetailedDB):
        self.check_possible_duplicate(location)

    async def get(self, id: PydanticObjectId) -> LocationDetailedDB | None:
        return await LocationDetailedDB.get(id)

    async def get_bbox_short(self, bbox: BoundingBox, activities: list[str] | None) -> list[LocationShortDB]:
        filters = [
            { "location": { "$geoWithin": { "$box":  bbox }}}
            # TODO: When PR https://github.com/roman-right/beanie/pull/552 merged, use this line instead
            # Box(LocationShort.location, lower_left=bbox[0], upper_right=bbox[1])
        ]
        if activities is not None:
            filters.append(In(LocationShortDB.activity_type, activities))

        return await LocationShortDB.find_many(*filters).to_list()

    def check_possible_duplicate(self, location: LocationDetailedDB) -> None | list[LocationDetailedDB]:
        return None



