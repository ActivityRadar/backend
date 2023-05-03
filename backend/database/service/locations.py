from beanie import PydanticObjectId
from beanie.operators import Box, In, NearSphere

from backend.database.models.locations import LocationDetailedDB, LocationShortDB
from backend.util.types import BoundingBox, LongLat

class LocationService:
    def __init__(self) -> None:
        # take care, the ODM classes might not have been initialized by beanie yet...
        # print(dir(LocationDetailed.find_all()))
        return

    def get_activities_filter(self, activities):
        return In(LocationShortDB.activity_type, activities)

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
            filters.append(self.get_activities_filter(activities))

        return await LocationShortDB.find_many(*filters).to_list()

    async def get_around(self, center: LongLat, radius: float, activities: list[str] | None) -> list[LocationShortDB]:
        if radius == 0.0:
            return []

        filters = [NearSphere(LocationShortDB.location, center[0], center[1], max_distance=radius)]
        if activities is not None:
            filters.append(self.get_activities_filter(activities))

        return await LocationShortDB.find_many(*filters).to_list()

    def check_possible_duplicate(self, location: LocationDetailedDB) -> None | list[LocationDetailedDB]:
        return None



