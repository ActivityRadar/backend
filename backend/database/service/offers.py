from datetime import datetime

from beanie import PydanticObjectId
from beanie.odm.operators.find import BaseFindOperator
from beanie.odm.operators.find.comparison import Eq, In, NotIn
from beanie.operators import Near, Not

from backend.database.models.locations import (
    LocationDetailedDB,
    LocationShort,
    LocationShortDB,
)
from backend.database.models.offers import (
    Offer,
    OfferCreatorInfo,
    OfferIn,
    OfferLocationConnected,
    OfferStatus,
    OfferTime,
    OfferType,
    OfferVisibility,
)
from backend.database.models.users import User
from backend.util import errors
from backend.util.types import LongLat, TimeSlotFixed


class TimesMatcher:
    def match(self, lhs: OfferTime, rhs: OfferTime):
        l_type, r_type = lhs.type, rhs.type
        if OfferType.FLEXIBLE in [l_type, r_type]:
            return True

        if lhs.type == OfferType.SINGLE and rhs.type == OfferType.SINGLE:
            return self._one_to_one(lhs.times, rhs.times)

        # Should not happen...
        return False

    def _one_to_one(self, time1: TimeSlotFixed, time2: TimeSlotFixed):
        s1, e1, s2, e2 = [*time1, *time2]
        return s1 <= s2 <= e1 or s2 <= s1 <= e2


class OfferService:
    tm = TimesMatcher()

    async def create(self, user: User, offer: OfferIn) -> PydanticObjectId:
        # TODO: check if user is eligible to create an offer.

        location = offer.location
        if isinstance(location, OfferLocationConnected):
            loc = await LocationShortDB.get(location.id)
            if not loc:
                raise errors.LocationDoesNotExist()
            location.coords = loc.location

        new_offer = await Offer(
            creation_date=datetime.utcnow(),
            user_info=OfferCreatorInfo(**user.dict()),
            status=OfferStatus.OPEN,
            **offer.dict(),
        ).insert()

        return new_offer.id

    async def _check_and_set_timeout(self, offers) -> list[Offer]:
        now = datetime.utcnow()

        filtered_offers = []
        for offer in offers:
            # TODO: handle timeout case with recurrence
            if offer.time.type == OfferType.SINGLE and offer.time.times[1] < now:
                offer.status = OfferStatus.TIMEOUT
                await offer.save()

            if offer.status == OfferStatus.TIMEOUT:
                continue

            filtered_offers.append(offer)

        return filtered_offers

    def _filter_date_time(
        self, offers: list[Offer], date_time: OfferTime | None
    ) -> list[Offer]:
        if not date_time or date_time.type == OfferType.FLEXIBLE:
            return offers

        return [offer for offer in offers if self.tm.match(offer.time, date_time)]

    async def _get_with_filters(
        self, user: User, filters: list[BaseFindOperator]
    ) -> list[Offer]:
        filters.extend(
            [
                Eq(Offer.status, OfferStatus.OPEN),
                Eq(Offer.visibility, OfferVisibility.PUBLIC),
                Offer.user_info.id != user.id,
            ]
        )

        # TODO: imeplement users ignoring eachother's offers
        # ignored = []  # user.ignored
        # if ignored:
        #     filters.append(NotIn(Offer.user_info.user_id, ignored))

        # TODO: account for FRIENDS visibility
        # problem: have to access friendship collection
        # One approach might be, loading all friends of the user once, and then
        # using the In operator for the offer's user_id and that list...
        # Or(Eq(Offer.visibility, OfferVisibility.PUBLIC),
        # And(Eq(Offer.visibility, OfferVisibility.FRIENDS))),

        offers = await Offer.find(*filters).to_list()
        offers = await self._check_and_set_timeout(offers)

        return offers

    async def get(self, ids: list[PydanticObjectId]) -> list[Offer]:
        offers = await Offer.find(In(Offer.id, ids)).to_list()

        return offers

    async def get_at_location(
        self, user: User, location_id: PydanticObjectId, date_time: OfferTime
    ) -> list[Offer]:
        loc = await LocationDetailedDB.get(location_id)
        if not loc:
            raise errors.LocationDoesNotExist()

        filters: list[BaseFindOperator] = [
            Eq(Offer.location.id, location_id),
        ]

        offers = await self._get_with_filters(user, filters)

        return self._filter_date_time(offers, date_time)

    async def get_around(
        self,
        user: User,
        center: LongLat,
        distance: float,  # in meters
        time: OfferTime,
        activities: list[str] | None,
    ) -> list[Offer]:
        filters: list[BaseFindOperator] = [
            Near(Offer.location.coords, *center, max_distance=distance),
        ]

        if activities:
            filters.append(In(Offer.activity, activities))

        offers = await self._get_with_filters(user, filters)

        return self._filter_date_time(offers, time)

    async def _get_offer_with_checks(
        self, user: User, offer_id: PydanticObjectId
    ) -> Offer:
        offer = await Offer.get(offer_id)
        if not offer:
            raise errors.OfferDoesNotExist()

        if offer.user_info.id != user.id:
            raise errors.UserDoesNotOwnOffer()

        return offer

    async def set_status(
        self, user: User, offer_id: PydanticObjectId, status: OfferStatus
    ):
        offer = await self._get_offer_with_checks(user, offer_id)

        # TODO: actions connected to status change

        offer.status = status
        await offer.save()

    async def delete(self, user: User, offer_id: PydanticObjectId):
        offer = await self._get_offer_with_checks(user, offer_id)

        # TODO: notify potential partners that the offer has been closed

        await offer.delete()