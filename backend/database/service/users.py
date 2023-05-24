from datetime import datetime, timedelta
import math
from typing import Any

from beanie import PydanticObjectId
from beanie.odm.queries.find import FindMany
from beanie.operators import All, ElemMatch, In, RegEx

from backend.database.models.shared import PhotoInfo
from backend.database.models.users import (
    AuthType,
    Authentication,
    RelationStatus,
    User,
    UserIn,
    UserPasswordReset,
    UserRelation,
)
from backend.util.auth import (
    ChangePasswordForm,
    ResetPasswordForm,
    create_password_reset_token,
    decode_password_reset_token,
    hash_password,
    verify_password,
)
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

    async def find_by_name(self, name):
        # TODO: Check if this can be exploited! (like some injection, idk)
        regex = "^" + name # only search from start of username
        users = await User.find_many(RegEx(User.username, regex, options="i")).to_list()
        return users

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

    async def change_password(self, user: User, form: ChangePasswordForm):
        if not verify_password(form.old_password, user.authentication.password_hash):
            raise E.UserWrongPassword()

        if form.old_password == form.new_password:
            raise E.UserNewPasswordIsOldPassword()

        await self.reset_password(user, ResetPasswordForm(**form.dict()))

    async def reset_password(self, user: User, form: ResetPasswordForm):
        if form.new_password != form.new_password_repeated:
            raise E.UserNewPasswordDoesNotMatch()

        await self._set_password(user, form.new_password)

    async def _set_password(self, user: User, new_password: str):
        user.authentication.password_hash = hash_password(new_password)
        await user.save()

    async def request_reset_password(self, username: str):
        user = await self.get_by_username(username)
        if not user:
            # pretend that everything went alright
            raise E.UserDoesNotExist()

        token, expiry = create_password_reset_token({ "sub": str(user.id) })
        print(token)

        # if the user has an ongoing reset process, decline the request
        u = await UserPasswordReset.find_one(UserPasswordReset.id == user.id)
        if u:
            raise E.UserHasPendingRequest()

        # TODO: remember the IP address of the issuer to prevent spam requests and unnecessary emails to users
        await UserPasswordReset(
            username=username,
            expiry=expiry,
            token=token,
            ip_address=None
        ).save()

        # TODO: send an email to the email address of the user with a hash that enables
        # the user to use the reset_password option

    async def execute_password_reset(self, token: str, passwords: ResetPasswordForm):
        # check if the token is valid
        token_info = decode_password_reset_token(token)

        # check if the token belongs to the user's current reset process
        u = await UserPasswordReset.find_one(UserPasswordReset.id == token_info.id)
        if u is None or u.token != token:
            raise E.TokenInvalid()

        user = await self.get_by_username(u.username)
        if not user:
            # This should never be triggered though...
            # Except, the user was deleted in the meantime...
            raise E.UserDoesNotExist()

        await self.reset_password(user, passwords)

        # delete the reset request after successful reset
        await u.delete()

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
                case _:
                    raise E.InvalidUpdateOption(k)

        for k, v in change_set.items():
            await _do(k, v)

        await user.save()
        return user

class RelationService:
    async def add_friend(self, from_user: User, to_user: User):
        ids: list[PydanticObjectId] = [from_user.id, to_user.id] # type: ignore

        f = await UserRelation.find_one(All(UserRelation.users, ids))
        if f is not None:
            raise E.RelationExists(f.id)

        f = await UserRelation(
            users=ids,
            creation_date=datetime.utcnow(),
            status=RelationStatus.PENDING
        ).insert()

        # TODO: Send a request

        return f.id

    async def get_relation(self, relation_id: PydanticObjectId):
        f = await UserRelation.get(relation_id)
        if not f:
            raise E.RelationDoesNotExist()

        return f

    async def get_open_request(self, relation_id: PydanticObjectId):
        f = await self.get_relation(relation_id)
        if f.status != RelationStatus.PENDING:
            raise E.NotAnOpenRequest(f.id)

        return f

    def check_user_in_relation(self, user: User, relation: UserRelation):
        if not user.id in relation.users:
            raise E.UserIsNotPartOfRelation(user.id, relation.id)

    async def accept_friend_request(self, user: User, relation_id: PydanticObjectId):
        f = await self.get_open_request(relation_id)
        self.check_user_in_relation(user, f)
        f.status = RelationStatus.ACCEPTED
        await f.save()

        # TODO: Inform requesting user

    async def decline_friend_request(self, user: User, relation_id: PydanticObjectId):
        f = await self.get_open_request(relation_id)
        self.check_user_in_relation(user, f)
        f.status = RelationStatus.DECLINED
        await f.save()

        # TODO: Inform requesting user

    async def get_all_relations(self, user: User):
        fs = await UserRelation.find(ElemMatch(UserRelation.users, user.id)) # type: ignore
        return fs

    async def get_all_active_relations(self, user: User):
        fs = await self.get_all_relations(user)
        return await fs.find(UserRelation.status == RelationStatus.ACCEPTED)
