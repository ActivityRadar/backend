from datetime import datetime

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq
from beanie.operators import Box, In, Near, Pop, Pull, Push

from backend.database.models.locations import (
    LocationDetailed,
    LocationDetailedDb,
    LocationHistory,
    LocationHistoryIn,
    LocationShortDb,
    LocationUpdateReport,
    Review,
    ReviewWithId,
    TagChangeType,
)
from backend.database.models.shared import CreationInfo, LocationCreators, PhotoInfo
from backend.database.models.users import User
from backend.util import errors
from backend.util.types import BoundingBox, LongLat

MAX_ONGOING_UPDATE_REPORTS = 10
MAX_RECENT_REVIEWS = 5


class LocationService:
    def __init__(self) -> None:
        # take care, the ODM classes might not have been initialized by beanie yet...
        # print(dir(LocationDetailed.find_all()))
        return

    def get_activities_filter(self, activities):
        return In(LocationShortDb.activity_types, activities)

    async def _insert(self, location: LocationDetailedDb):
        loc = await location.insert()
        await LocationShortDb(
            **loc.dict(), average_rating=loc.reviews.average_rating
        ).insert()
        return loc

    async def insert(
        self, location: LocationDetailed, user_id: PydanticObjectId
    ) -> PydanticObjectId:
        self.check_possible_duplicate(location)

        creation = CreationInfo(
            created_by=LocationCreators.APP, date=datetime.now(), user_id=user_id
        )
        loc = LocationDetailedDb(
            **location.dict(), last_modified=creation.date, creation=creation
        )
        loc = await self._insert(loc)

        return loc.id

    async def get(self, id: PydanticObjectId) -> LocationDetailedDb | None:
        return await LocationDetailedDb.get(id)

    async def get_short(self, id: PydanticObjectId) -> LocationShortDb | None:
        return await LocationShortDb.get(id)

    async def get_bbox_short(
        self, bbox: BoundingBox, activities: list[str] | None
    ) -> list[LocationShortDb]:
        return await self.find_with_filters(
            Box(
                LocationShortDb.location,
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
    ) -> list[LocationDetailedDb]:
        if radius and radius < 1 or limit == 0:
            return []

        return await self.find_with_filters(
            Near(
                LocationDetailedDb.location, center[0], center[1], max_distance=radius
            ),
            activities=activities,
            limit=limit,
            return_short=False,
        )

    async def find_with_filters(
        self,
        *filters,
        activities: list[str] | None,
        limit: int | None = None,
        return_short=True,
    ) -> list[LocationDetailedDb] | list[LocationShortDb]:
        filters = list(filters)
        if activities is not None:
            filters.append(self.get_activities_filter(activities))

        if return_short:
            return await LocationShortDb.find_many(*filters).limit(limit).to_list()

        return await LocationDetailedDb.find_many(*filters).limit(limit).to_list()

    def check_possible_duplicate(
        self, location: LocationDetailed
    ) -> None | list[LocationDetailed]:
        return None

    async def update(self, user: User, history: LocationHistoryIn):
        # TODO: Acquire a write lock, so between reading the location data
        # and writing them there cant be another update...
        loc = await LocationDetailedDb.get(history.location_id)
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
        await LocationShortDb(**loc.dict()).save()
        # loc_short = await LocationShortDb.get(location_id)

        # TODO: add location history entry
        await history.save()

    def _update(self, location: LocationDetailedDb, history: LocationHistory):
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

    async def add_photo(
        self, user: User, location_id: PydanticObjectId, photo: PhotoInfo
    ):
        location = await self.get(location_id)
        if not location:
            raise errors.LocationDoesNotExist()

        photos_by_user = [p for p in location.photos if p.user_id == user.id]

        if len(photos_by_user) >= 3:
            raise errors.UserPostedTooManyPhotos()

        if user.id != photo.user_id:
            raise Exception("Profile photo does not belong to user!")

        if location.photos is None:
            location.photos = [photo]
            await location.save()
        else:
            await location.update(Push({LocationDetailedDb.photos: photo}))

    async def get_photo_owner(self, location_id: PydanticObjectId, photo_url: str):
        loc: LocationDetailedDb = await self.get(location_id)
        photo = [p for p in loc.photos if p.url == photo_url]
        if len(photo) != 1:
            raise errors.PhotoDoesNotExist()

        photo = photo[0]
        return photo.user_id

    async def remove_photo(self, location_id: PydanticObjectId, photo_url: str):
        loc: LocationDetailedDb = await self.get(location_id)
        await loc.update(Pull({LocationDetailedDb.photos: Eq("url", photo_url)}))

    async def add_review(self, location_id: PydanticObjectId, review: Review):
        loc = await self.get(location_id)
        if not loc:
            raise errors.LocationDoesNotExist()

        former_avg = loc.reviews.average_rating
        cnt = loc.reviews.count

        # TODO: is this accurate? Floating point inaccuracies might be a problem
        new_avg = (former_avg * cnt + review.overall_rating) / (cnt + 1)

        loc.reviews.average_rating = new_avg
        loc.reviews.count += 1
        loc = await loc.save()

        print(len(loc.reviews.recent))
        await loc.update(
            Push(
                {
                    LocationDetailedDb.reviews.recent: {
                        "$position": 0,
                        "$each": [ReviewWithId(**review.dict())],
                    }
                }
            )
        )  # push first
        if len(loc.reviews.recent) == MAX_RECENT_REVIEWS:
            loc = await loc.update(
                Pop({LocationDetailedDb.reviews.recent: 1})
            )  # pop last
        print(len(loc.reviews.recent))

        loc_short = await self.get_short(location_id)
        if not loc_short:
            raise errors.LocationDoesNotExist()

        loc_short.average_rating = new_avg

    async def remove_review(self, location_id: PydanticObjectId, review: Review):
        loc = await self.get(location_id)
        if not loc:
            raise errors.LocationDoesNotExist()

        # adjust count and average
        former_avg = loc.reviews.average_rating
        cnt = loc.reviews.count

        if cnt == 1:
            new_avg = 0
            loc.reviews.count = 0
        else:
            new_avg = (former_avg * cnt - review.overall_rating) / (cnt - 1)
            loc.reviews.count -= 1

        loc.reviews.average_rating = new_avg
        loc = await loc.save()

        # update short version
        loc_short = await self.get_short(location_id)
        if not loc_short:
            raise errors.LocationDoesNotExist()

        # remove from recent list if present
        if review in loc.reviews.recent:
            loc = await loc.update(
                Pull({LocationDetailedDb.reviews.recent: Eq("id", review.id)})
            )
            # TODO: in this case add another recent Review to the list

    async def update_review(
        self, location_id: PydanticObjectId, updated_review: Review, old_rating: float
    ):
        loc = await self.get(location_id)
        if not loc:
            raise errors.LocationDoesNotExist()

        # adjust count and average
        former_avg = loc.reviews.average_rating
        cnt = loc.reviews.count

        # add new rating and substract old rating from former average
        new_avg = (former_avg * cnt + updated_review.overall_rating - old_rating) / cnt

        loc.reviews.average_rating = new_avg

        new_review = ReviewWithId(**updated_review.dict())

        # check if the updated review was in the recent list
        try:
            r_ids = [r.id for r in loc.reviews.recent]
            idx = r_ids.index(new_review.id)
            loc.reviews.recent[idx] = new_review
        except ValueError:
            # If there is a ValueError, we ignore it, as it is expected
            pass
        finally:
            await loc.save()
