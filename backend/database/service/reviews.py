from beanie import PydanticObjectId
from beanie.operators import And, ElemMatch, Eq

from backend.database.models.shared import Review
from backend.database.models.users import User
from backend.util import errors


class ReviewService:
    async def get(self, id: PydanticObjectId):
        return await Review.get(id)

    async def create(self, user: User, location_id: PydanticObjectId, review: Review):
        u = await Review.find_one(And(Eq(Review.user_id, user.id), Eq(Review.location_id, location_id)))

        # error if user has review for location already
        if u:
            raise errors.UserHasReviewAlready

        # TODO: check if review is appropriate for location
        # error if data is incomplete or incorrect

        review.user_id = user.id # type: ignore
        r = await review.insert()
        return r.id

