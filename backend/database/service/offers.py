import math
import random
from datetime import datetime

from beanie import PydanticObjectId
from beanie.odm.operators.find import BaseFindOperator
from beanie.odm.operators.find.comparison import Eq, In
from beanie.odm.queries.aggregation import AggregationQuery
from beanie.operators import Near, Push
from geopy import distance as geo_distance

from backend.database.models.locations import LocationDetailedDb, LocationShortDb
from backend.database.models.offers import (
    LocationBlurrOut,
    Offer,
    OfferCreatorInfo,
    OfferIn,
    OfferLocationConnected,
    OfferStatus,
    OfferTime,
    OfferType,
    OfferVisibility,
    Participant,
    ParticipantStatus,
)
from backend.database.models.shared import GeoJsonLocation
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


def blurr_center(center: GeoJsonLocation, radius: float):
    radius_meters = radius * 1000
    rand_radius = math.sqrt(random.uniform(0, 1)) * radius_meters
    angle = 2 * math.pi * random.random()

    long, lat = center.coordinates
    meters_per_degree = 111000.0
    lat_adjustment = rand_radius / meters_per_degree * math.cos(angle)
    long_adjustment = (
        rand_radius
        / (meters_per_degree * math.cos(math.radians(long)))
        * math.sin(angle)
    )

    return GeoJsonLocation(
        type="Point", coordinates=[long + long_adjustment, lat + lat_adjustment]
    )


class OfferService:
    tm = TimesMatcher()

    async def create(self, user: User, offer: OfferIn) -> Offer:
        # TODO: check if user is eligible to create an offer.

        location = offer.location
        if isinstance(location, OfferLocationConnected):
            loc = await LocationShortDb.get(location.id)
            if not loc:
                raise errors.LocationDoesNotExist()
            location.coords = loc.location

        participants = [Participant(id=user.id, status=ParticipantStatus.HOST)]

        blurr = LocationBlurrOut(
            radius=offer.blurr.radius,
            center=blurr_center(
                center=offer.location.coords, radius=offer.blurr.radius
            ),
        )

        new_offer = await Offer(
            creation_date=datetime.utcnow(),
            user_info=OfferCreatorInfo(**user.dict()),
            status=OfferStatus.OPEN,
            participants=participants,
            blurr_info=blurr,
            **offer.dict(),
        ).insert()

        return new_offer

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

        offers = await Offer.find_many(*filters).to_list()
        offers = await self._check_and_set_timeout(offers)

        return offers

    async def get(self, id: PydanticObjectId) -> Offer | None:
        return await Offer.get(id)

    async def get_bulk(self, ids: list[PydanticObjectId]) -> list[Offer]:
        offers = await Offer.find(In(Offer.id, ids)).to_list()

        return offers

    async def get_at_location(
        self, user: User, location_id: PydanticObjectId, date_time: OfferTime
    ) -> list[Offer]:
        loc = await LocationDetailedDb.get(location_id)
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
        distance: float,  # in km
        time: OfferTime,
        activities: list[str] | None,
    ) -> list[Offer]:
        filters: list[BaseFindOperator] = [
            # use this: when beanie/#674 is fixed!
            # Near(Offer.blurr_info.center, *center, max_distance=distance * 1000),
            Near("blurr_info.center", *center, max_distance=distance * 1000),
        ]

        if activities:
            filters.append(In(Offer.activity, activities))

        offers = await self._get_with_filters(user, filters)

        # TODO: filter out offers with too low visibility radius
        # maybe as in https://stackoverflow.com/questions/28659081/mongodb-near-geonear-with-the-maxdistance-value-from-database
        result = []
        for offer in offers:
            dist = geo_distance.distance(offer.blurr_info.center.coordinates, center).km
            if offer.visibility_radius + offer.blurr_info.radius < dist:
                continue

            result.append(offer)

        return self._filter_date_time(result, time)

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

    async def request_to_join(
        self, user: User, offer_id: PydanticObjectId, message: str
    ):
        offer = await self.get(offer_id)

        if offer is None:
            raise errors.UserAlreadyRequestedToJoin()

        await offer.update(
            Push(
                {
                    Offer.participants: Participant(
                        id=user.id, status=ParticipantStatus.REQUESTED
                    )
                }
            )
        )

        # TODO: send push notification to host with message

    async def decline_request(
        self, host: User, offer_id: PydanticObjectId, participant_id: PydanticObjectId
    ):
        self._set_participant_status(
            host=host,
            offer_id=offer_id,
            participant_id=participant_id,
            status=ParticipantStatus.DECLINED,
        )

    async def accept_request(
        self, host: User, offer_id: PydanticObjectId, participant_id: PydanticObjectId
    ):
        self._set_participant_status(
            host=host,
            offer_id=offer_id,
            participant_id=participant_id,
            status=ParticipantStatus.ACCEPTED,
        )

    async def _set_participant_status(
        self,
        host: User,
        offer_id: PydanticObjectId,
        participant_id: PydanticObjectId,
        status: ParticipantStatus,
    ):
        offer = await self.get(offer_id)
        if not offer:
            raise errors.OfferDoesNotExist()

        if offer.user_info.id != host.id:
            raise errors.UserDoesNotOwnOffer()

        for p in offer.participants:
            if p.id != participant_id:
                continue

            if p.status == status:
                raise errors.ParticipantStatusUnchanged()

            p.status = status
            await offer.save()
            break
        else:
            raise errors.UserIsNotParticipant()
