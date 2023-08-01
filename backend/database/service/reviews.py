from datetime import datetime

from beanie import PydanticObjectId

from backend.database.models.locations import Review, ReviewBase, ReviewReport
from backend.database.models.users import User
from backend.database.service.locations import LocationService
from backend.util import errors


class ReviewService:
    location_service = LocationService()

    async def get(self, id: PydanticObjectId):
        return await Review.get(id)

    async def get_page(self, location_id: PydanticObjectId, offset: int, size: int):
        rs = (
            await Review.find(Review.location_id == location_id)
            .skip(offset)
            .limit(size)
            .to_list()
        )
        if len(rs) < size:
            return rs, None
        return rs, offset + size

    def validate(self, review_info: ReviewBase):
        # TODO: implement this!
        # - text is valid and not too long
        # - details fit the location type
        pass

    async def create(self, user: User, review_info: ReviewBase):
        u = await Review.find_one(
            Review.user_id == user.id and Review.location_id == review_info.location_id
        )

        # error if user has review for location already
        if u:
            raise errors.UserHasReviewAlready()

        self.validate(review_info)

        review = await Review(
            user_id=user.id, creation_date=datetime.utcnow(), **review_info.dict()
        ).insert()

        await self.location_service.add_review(review_info.location_id, review)

        return review.id

    async def update(self, user: User, review_id: PydanticObjectId, review: ReviewBase):
        r = await Review.get(review_id)
        if not r:
            raise errors.ReviewDoesNotExist()

        if r.user_id != user.id:
            raise errors.UserDoesNotOwnReview()

        old_rating = r.overall_rating
        # TODO: validate new review info
        self.validate(review)

        # adjust all values from the new review info
        for k, v in review.dict().items():
            r.__setattr__(k, v)

        r.creation_date = datetime.utcnow()
        await r.save()

        await self.location_service.update_review(
            r.location_id, r, old_rating=old_rating
        )

    async def confirm_location(
        self, user: User, location_id: PydanticObjectId, confirm: bool
    ):
        # error if location not found
        # error if user has same confirmation for location already
        raise NotImplementedError()

    async def delete(self, user: User, review_id: PydanticObjectId):
        r = await Review.get(review_id)
        if not r:
            raise errors.ReviewDoesNotExist()

        if r.user_id != user.id:
            raise errors.UserDoesNotOwnReview()

        await r.delete()

        await self.location_service.remove_review(r.location_id, r)

    async def report(self, user: User, review_id: PydanticObjectId, reason: str):
        report = ReviewReport.find_one(
            ReviewReport.user_id == user.id and ReviewReport.review_id == review_id
        )

        if report:
            raise errors.UserHasAlreadyReportedThisReview()

        r = await ReviewReport(
            user_id=user.id,
            review_id=review_id,
            report_date=datetime.utcnow(),
            reason=reason,
        ).insert()

        # TODO: notify admin of report to check on it

        return r.id
