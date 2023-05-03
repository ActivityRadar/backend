from beanie import PydanticObjectId
from beanie.operators import Box, In

from backend.database.models.locations import LocationDetailed, LocationShort
from backend.util.types import BoundingBox

class LocationService:
    def __init__(self) -> None:
        # take care, the ODM classes might not have been initialized by beanie yet...
        # print(dir(LocationDetailed.find_all()))
        return

    def insert(self, location: LocationDetailed):
        self.check_possible_duplicate(location)

    async def get(self, id: PydanticObjectId) -> LocationDetailed | None:
        return await LocationDetailed.get(id)

    async def get_bbox_short(self, bbox: BoundingBox, activities: list[str] | None) -> list[LocationShort]:
        filters = [
            { "location": { "$geoWithin": { "$box":  bbox }}}
            # TODO: When PR https://github.com/roman-right/beanie/pull/552 merged, use this line instead
            # Box(LocationShort.location, lower_left=bbox[0], upper_right=bbox[1])
        ]
        if activities is not None:
            filters.append(In(LocationShort.activity_type, activities))

        return await LocationShort.find_many(*filters).to_list()

    def check_possible_duplicate(self, location: LocationDetailed) -> None | list[LocationDetailed]:
        return None



