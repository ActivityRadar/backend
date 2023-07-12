from datetime import datetime

from beanie import PydanticObjectId
from beanie.operators import Box, In, Near

from backend.database.models.locations import (
    LocationDetailed,
    LocationDetailedDB,
    LocationHistory,
    LocationHistoryIn,
    LocationShortDB,
    LocationUpdateReport,
    TagChangeType,
)
from backend.database.models.shared import CreationInfo, LocationCreators, PhotoInfo
from backend.database.models.users import User
from backend.util import errors
from backend.util.types import BoundingBox, LongLat

MAX_ONGOING_UPDATE_REPORTS = 10


class LocationService:
    def __init__(self) -> None:
        # take care, the ODM classes might not have been initialized by beanie yet...
        # print(dir(LocationDetailed.find_all()))
        return

    def get_activities_filter(self, activities):
        return In(LocationShortDB.activity_type, activities)

    async def insert(
        self, location: LocationDetailed, user_id: PydanticObjectId
    ) -> PydanticObjectId:
        self.check_possible_duplicate(location)

        creation = CreationInfo(
            created_by=LocationCreators.APP, date=datetime.now(), user_id=user_id
        )
        loc = await LocationDetailedDB(
            **location.dict(), last_modified=creation.date, creation=creation
        ).insert()
        await LocationShortDB(**loc.dict()).insert()
        return loc.id

    async def get(self, id: PydanticObjectId) -> LocationDetailedDB | None:
        return await LocationDetailedDB.get(id)

    async def get_bbox_short(
        self, bbox: BoundingBox, activities: list[str] | None
    ) -> list[LocationShortDB]:
        return await self.find_with_filters(
            Box(
                LocationShortDB.location,
                lower_left=list(bbox[0]),
                upper_right=list(bbox[1]),
            ),
            activities=activities,
        )

    async def get_around(
        self,
        center: LongLat,
        activities: list[str] | None,
        radius: float | None,
        limit: int,
    ) -> list[LocationShortDB]:
        if radius and radius < 1 or limit == 0:
            return []

        return await self.find_with_filters(
            Near(LocationShortDB.location, center[0], center[1], max_distance=radius),
            activities=activities,
            limit=limit,
        )

    async def find_with_filters(
        self, *filters, activities: list[str] | None, limit: int | None = None
    ):
        filters = list(filters)
        if activities is not None:
            filters.append(self.get_activities_filter(activities))

        return await LocationShortDB.find_many(*filters).limit(limit).to_list()

    def check_possible_duplicate(
        self, location: LocationDetailed
    ) -> None | list[LocationDetailed]:
        return None

    async def set_average_rating(
        self, location_id: PydanticObjectId, average: float | None
    ):
        loc = await self.get(location_id)
        if not loc:
            raise errors.LocationDoesNotExist()

        loc.average_rating = average
        await loc.save()

        return loc.average_rating

    async def update(self, user: User, history: LocationHistoryIn):
        # TODO: Acquire a write lock, so between reading the location data
        # and writing them there cant be another update...
        loc = await LocationDetailedDB.get(history.location_id)
        if not loc:
            raise errors.LocationDoesNotExist()

        # TODO: determine if the user is eligible to update the location

        history = LocationHistory(
            user_id=user.id,
            date=datetime.utcnow(),
            **history.dict(),
        )
        self._update(loc, history)
        await loc.save()

        # Update the short version
        await LocationShortDB(**loc.dict()).save()
        # loc_short = await LocationShortDB.get(location_id)

        # TODO: add location history entry
        await history.save()

    def _update(self, location: LocationDetailedDB, history: LocationHistory):
        if history.after is not None:
            if history.before is None:
                raise errors.InvalidHistory()

            for k, v in history.after.items():
                if k not in ["name", "geometry", "activity_type", "location"]:
                    raise errors.InvalidUpdateType(k)

                if k not in history.before:
                    raise errors.InvalidHistory()

                v_old = history.before[k]

                if v_old != location.__getattribute__(k):
                    raise errors.InvalidBeforeData(k)

                location.__setattr__(k, v)

        if history.tags is not None:
            tags = location.tags
            for t, change in history.tags.items():
                match change.mode:
                    case TagChangeType.ADD:
                        if t in tags:
                            raise errors.TagExists()
                        tags[t] = change.content
                    case TagChangeType.DELETE:
                        if t not in tags:
                            raise errors.TagDoesNotExist()

                        if change.content != tags[t]:
                            raise errors.InvalidBeforeData(f"tags:{t}")

                        del tags[t]
                    case TagChangeType.CHANGE:
                        if t not in tags:
                            raise errors.TagDoesNotExist()

                        if tags[t] != change.content[0]:
                            raise errors.InvalidBeforeData(t)

                        tags[t] = change.content[1]

    async def add_photo(
        self, user: User, location_id: PydanticObjectId, photo: PhotoInfo
    ):
        raise NotImplementedError()

    async def get_history(self, location_id: PydanticObjectId, offset: int):
        search = LocationHistory.find(LocationHistory.location_id == location_id)
        return await search.sort(-LocationHistory.date).skip(offset).limit(10).to_list()

    async def report_update(self, user: User, update_id: PydanticObjectId, reason: str):
        c = await LocationUpdateReport.find(
            LocationUpdateReport.user_id == user.id
        ).count()
        if c > MAX_ONGOING_UPDATE_REPORTS:
            raise errors.UserHasTooManyOngoingUpdateReports()

        # TODO: Sanitize reason

        # TODO: notify moderator

        r = await LocationUpdateReport(
            user_id=user.id, date=datetime.utcnow(), reason=reason, update_id=update_id
        ).insert()

        return r.id
