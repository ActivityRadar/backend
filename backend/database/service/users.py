import math

from backend.database.models.users import User
from backend.util.errors import UserDoesNotExist, UserLowTrust
from backend.util.types import LocationTrustScore, UserTrustScore

CREATOR_TO_LOCATION_SCORES: dict[UserTrustScore, LocationTrustScore] = {
    1: 1,
    2: 10,
    3: 100,
    4: 1000,
}

class UserService:
    async def check_eligible_to_add(self, user_id) -> LocationTrustScore:
        u = await User.get(user_id)
        if u is None:
            raise UserDoesNotExist()
        if u.trust_score < 100:
            raise UserLowTrust()

        return CREATOR_TO_LOCATION_SCORES[math.floor(math.log10(u.trust_score))]

