from datetime import datetime
import math
from typing import Any

from backend.database.models.users import AuthType, Authentication, User, UserIn
from backend.util.auth import hash_password
from beanie import PydanticObjectId
from backend.database.models.shared import PhotoInfo
import backend.util.errors as E
from backend.util.types import LocationTrustScore, UserTrustScore

CREATOR_TO_LOCATION_SCORES: dict[UserTrustScore, LocationTrustScore] = {
    1: 1,
    2: 10,
    3: 100,
    4: 1000,
}

INITIAL_TRUST_SCORE = 100
USER_ARCHIVE_DAYS = 14

class UserService:
    async def check_eligible_to_add(self, user_id) -> LocationTrustScore:
        u = await User.get(user_id)
        if u is None:
            raise E.UserDoesNotExist()
        if u.trust_score < 100:
            raise E.UserLowTrust()

        return CREATOR_TO_LOCATION_SCORES[math.floor(math.log10(u.trust_score))]

    def get_by_id(self, id: PydanticObjectId):
        return User.get(id)

    async def get_by_username(self, username: str) -> User | None:
        u = await User.find_one(User.username == username)
        return u

    async def create_user(self, user_info: UserIn):
        u = await self.get_by_username(user_info.username)
        if u:
            raise E.UserWithNameExists()

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

    async def archive(self, user: User) -> bool:
        if user.archived_until is not None:
            return False

        user.archived_until = datetime.utcnow() + timedelta(days=USER_ARCHIVE_DAYS)
        await user.save()

        # TODO: do actions connected to archiving a user:
        # - deactivate their offers and events
        # - disable conversations with on user's contacts' clients

        return True

    async def unarchive(self, user: User):
        if user.archived_until is None:
            return False

        user.archived_until = None
        await user.save()

        # TODO: do actions to reinstate the user normally
        # - reactivate offers
        # - enable all the user's conversations

        return True

    async def update_info(self, user: User, change_set: dict[str, Any]):
        async def _do(k, v):
            match k:
                case "username":
                    # v must be a username which is not taken yet
                    u = await self.get_by_username(v)
                    if u:
                        raise E.UsernameAlreadyTaken()

                    # TODO: check if last change was not too soon
                    # TODO: more checks for valid usernames
                    user.username = v
                case "display_name":
                    # TODO: v must be a valid display name
                    user.display_name = v
                case "email":
                    # TODO: v must be an email address as string
                    user.authentication.email = v
                    # TODO: the email is going to be confirmed
                case "avatar":
                    # v must be a dict convertible to a PhotoInfo object
                    if v is None:
                        avatar = None
                    else:
                        avatar = PhotoInfo(**v)

                    user.avatar = avatar

        for k, v in change_set.items():
            await _do(k, v)

        await user.save()
        return user

