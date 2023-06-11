from datetime import datetime

from beanie import PydanticObjectId
from beanie.operators import Box, In, NearSphere

from backend.database.models.locations import LocationDetailed, LocationDetailedDB, LocationShortDB
from backend.database.models.shared import CreationInfo, LocationCreators
from backend.util.types import BoundingBox, LongLat

class LocationService:
    def __init__(self) -> None:
        # take care, the ODM classes might not have been initialized by beanie yet...
        # print(dir(LocationDetailed.find_all()))
        return

    def get_activities_filter(self, activities):
        return In(LocationShortDB.activity_type, activities)

    async def insert(self, location: LocationDetailed, user_id: PydanticObjectId) -> PydanticObjectId:
        self.check_possible_duplicate(location)

        creation = CreationInfo(created_by=LocationCreators.APP, date=datetime.now(), user_id=user_id)
        loc = await LocationDetailedDB(**location.dict(), last_modified=creation.date, creation=creation).insert()
        await LocationShortDB(**loc.dict()).insert()
        return loc.id

    async def get(self, id: PydanticObjectId) -> LocationDetailedDB | None:
        return await LocationDetailedDB.get(id)

    async def get_bbox_short(self, bbox: BoundingBox, activities: list[str] | None) -> list[LocationShortDB]:
        return await self.find_with_filters(
            Box(LocationShortDB.location, lower_left=list(bbox[0]), upper_right=list(bbox[1])),
            activities=activities
        )

    async def get_around(self, center: LongLat, radius: float, activities: list[str] | None) -> list[LocationShortDB]:
        if radius == 0.0:
            return []

        return await self.find_with_filters(
            NearSphere(LocationShortDB.location, center[0], center[1], max_distance=radius),
            activities=activities
        )

    async def find_with_filters(self, *filters, activities: list[str] | None):
        filters = list(filters)
        if activities is not None:
            filters.append(self.get_activities_filter(activities))

        return await LocationShortDB.find_many(*filters).to_list()

    def check_possible_duplicate(self, location: LocationDetailed) -> None | list[LocationDetailed]:
        return None

    async def set_average_rating(self, location_id: PydanticObjectId, average: float | None):
        loc = await self.get(location_id)
        if not loc:
            raise errors.LocationDoesNotExist()

        loc.average_rating = average
        await loc.save()

        return loc.average_rating

