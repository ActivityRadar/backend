from datetime import datetime
import math

from backend.database.models.users import AuthType, Authentication, User, UserIn
from backend.util.auth import hash_password
from backend.util.errors import UserDoesNotExist, UserLowTrust, UserWithNameExists
from backend.util.types import LocationTrustScore, UserTrustScore

CREATOR_TO_LOCATION_SCORES: dict[UserTrustScore, LocationTrustScore] = {
    1: 1,
    2: 10,
    3: 100,
    4: 1000,
}

INITIAL_TRUST_SCORE = 100

class UserService:
    async def check_eligible_to_add(self, user_id) -> LocationTrustScore:
        u = await User.get(user_id)
        if u is None:
            raise UserDoesNotExist()
        if u.trust_score < 100:
            raise UserLowTrust()

        return CREATOR_TO_LOCATION_SCORES[math.floor(math.log10(u.trust_score))]

    async def get_by_username(self, username: str) -> User | None:
        u = await User.find_one(User.username == username)
        return u

    async def create_user(self, user_info: UserIn):
        u = await self.get_by_username(user_info.username)
        if u:
            raise UserWithNameExists()

        auth = Authentication(
            type=AuthType.PASSWORD,
            password_hash=hash_password(user_info.password),
            email=user_info.email
        )

        creation_time = datetime.utcnow()
        u = await User(
            **user_info.dict(),
            creation_date=creation_time,
            authentication=auth,
            trust_score=INITIAL_TRUST_SCORE
        ).insert()

        return u.id

