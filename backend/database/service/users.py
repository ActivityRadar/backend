import math
from datetime import datetime, timedelta
from typing import Any

from beanie import PydanticObjectId
from beanie.odm.queries.find import FindMany
from beanie.operators import All, ElemMatch, In, RegEx, Unset

import backend.util.errors as E
from backend.database.models.shared import PhotoInfo
from backend.database.models.users import (
    Authentication,
    AuthType,
    NewUser,
    RelationStatus,
    User,
    UserApiIn,
    UserPasswordReset,
    UserRelation,
    VerifyUserInfo,
)
from backend.util.crypto import (
    ChangePasswordForm,
    ResetPasswordForm,
    create_password_reset_token,
    decode_password_reset_token,
    generate_random_string,
    hash_password,
    verify_password,
)
from backend.util.types import LocationTrustScore, UserTrustScore

CREATOR_TO_LOCATION_SCORES: dict[UserTrustScore, LocationTrustScore] = {
    1: 1,
    2: 10,
    3: 100,
    4: 1000,
}

INITIAL_TRUST_SCORE = 100
USER_ARCHIVE_DAYS = 14
NEW_USER_VERIFICATION_MINUTES = 20


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

    async def get_bulk_by_id(self, ids: list[PydanticObjectId]) -> list[User]:
        return await User.find_many(In(User.id, ids)).to_list()

    async def get_by_username(self, username: str) -> User | None:
        u = await User.find_one(User.username == username)
        return u

    async def get_by_email(self, email: str) -> User | None:
        u = await User.find_one(User.authentication.email == email)
        return u

    async def find_by_name(self, name):
        # TODO: Check if this can be exploited! (like some injection, idk)
        regex = "^" + name  # only search from start of username
        users = await User.find_many(RegEx(User.username, regex, options="i")).to_list()
        return users

    async def create_user(self, user_info: UserApiIn) -> NewUser:
        u = await self.get_by_username(user_info.username)
        if u:
            raise E.UserWithNameExists()

        auth = Authentication(
            type=AuthType.PASSWORD,
            password_hash=hash_password(user_info.password),
            email=user_info.email,
        )

        random_string = generate_random_string(8)
        creation_time = datetime.utcnow()
        u = await NewUser(
            **user_info.dict(),
            creation_date=creation_time,
            authentication=auth,
            trust_score=INITIAL_TRUST_SCORE,
            verification_code=random_string,
            archived_until=datetime.utcnow()
            + timedelta(minutes=NEW_USER_VERIFICATION_MINUTES),
        ).insert()

        return u

    async def verify(self, verify_info: VerifyUserInfo) -> bool:
        """return false if the given code does not match."""
        u = await NewUser.find_one(NewUser.id == verify_info.id)
        if u is None:
            raise E.UserDoesNotExist()

        if u.archived_until is None:
            if u.verification_code is None:
                raise E.AlreadyVerified()
            raise Exception("User seems archived")

        if u.archived_until < datetime.utcnow():
            await u.delete()
            raise E.VerificationTimeout()

        if verify_info.verification_code != u.verification_code:
            return False

        await u.update(
            Unset({NewUser.archived_until: "", NewUser.verification_code: ""})
        )

        return True

    async def archive(self, user: User):
        if user.archived_until is not None:
            raise E.UserIsAlreadyArchived(archived_until=user.archived_until)

        user.archived_until = datetime.utcnow() + timedelta(days=USER_ARCHIVE_DAYS)
        await user.save()

        # TODO: do actions connected to archiving a user:
        # - deactivate their offers and events
        # - disable conversations with on user's contacts' clients

    async def unarchive(self, user: User):
        if user.archived_until is None:
            return False

        await user.update(Unset({User.archived_until: ""}))

        # TODO: do actions to reinstate the user normally
        # - reactivate offers
        # - enable all the user's conversations

        return True

    async def change_password(self, user: User, form: ChangePasswordForm):
        if not verify_password(form.old_password, user.authentication.password_hash):
            raise E.UserWrongPassword()

        if form.old_password == form.new_password:
            raise E.UserNewPasswordIsOldPassword()

        await self._set_password(user, form.new_password)

    async def reset_password(self, user: User, form: ResetPasswordForm):
        await self._set_password(user, form.new_password)

    async def _set_password(self, user: User, new_password: str):
        user.authentication.password_hash = hash_password(new_password)
        await user.save()

    async def request_reset_password(self, email: str):
        # TODO: requires each email address to be used only once!
        user = await self.get_by_email(email)
        if not user:
            # pretend that everything went alright
            raise E.UserDoesNotExist()

        token, expiry = create_password_reset_token({"sub": str(user.id)})
        print(token)

        # if the user has an ongoing reset process, decline the request
        u = await UserPasswordReset.find_one(UserPasswordReset.id == user.id)
        if u:
            raise E.UserHasPendingRequest()

        # TODO: remember the IP address of the issuer to prevent spam requests and unnecessary emails to users
        await UserPasswordReset(
            username=user.username, expiry=expiry, token=token, ip_address=None
        ).save()

        # TODO: send an email to the email address of the user with a hash that enables
        # the user to use the reset_password option

    async def execute_password_reset(self, token: str, reset_info: ResetPasswordForm):
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

        await self.reset_password(user, reset_info)

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

    async def put_photo(self, user: User, photo_info: PhotoInfo):
        if user.id != photo_info.user_id:
            raise Exception("Profile photo does not belong to user!")

        user.avatar = photo_info

        await user.save()

    async def delete_photo(self, user: User):
        user.avatar = None
        await user.save()

    async def report_avatar(self, reporter: User, reported: User):
        pass


class RelationService:
    async def add_friend(self, from_user: User, to_user: User):
        ids: list[PydanticObjectId] = [from_user.id, to_user.id]

        def send_request():
            # TODO: Send a request
            pass

        f = await UserRelation.find_one(All(UserRelation.users, ids))
        if f is None:
            f = await self._create(ids, RelationStatus.PENDING)
            send_request()

            return f.id

        match (f.status):
            case RelationStatus.ACCEPTED:
                raise E.RelationExists(f.id)
            case RelationStatus.DECLINED:
                # user has declined the request before, but now wants to accept.
                # In this case, we send another request to the initial requester
                if f.users[1] == from_user.id:
                    f.users.reverse()
                    await f.save()
                    send_request()
                    return f.id
                else:
                    raise E.UserCantSendAnotherRequestCurrently()
            case RelationStatus.PENDING:
                # both users probably requested simultaneously
                if f.users[1] == from_user.id:
                    await self.accept_friend_request(from_user, f.id)  # type: ignore
                # user sent request twice
                else:
                    raise E.UserHasPendingRequest()
            case RelationStatus.CHATTING:
                # users were only chatting until now
                # requesting user has to go first
                if from_user.id == f.users[1]:
                    f.users.reverse()
                f.status = RelationStatus.PENDING
                await f.save()
                send_request()
            case _:
                raise NotImplementedError()

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

    def check_user_is_not_requesting(self, user: User, relation: UserRelation):
        if user.id == relation.users[0]:
            raise E.UserCantReactToOwnRequest(user.id, relation.id)

    async def accept_friend_request(self, user: User, relation_id: PydanticObjectId):
        f = await self.get_open_request(relation_id)
        self.check_user_in_relation(user, f)
        self.check_user_is_not_requesting(user, f)
        f.status = RelationStatus.ACCEPTED
        await f.save()

        # TODO: Inform requesting user

    async def decline_friend_request(self, user: User, relation_id: PydanticObjectId):
        f = await self.get_open_request(relation_id)
        self.check_user_in_relation(user, f)
        self.check_user_is_not_requesting(user, f)
        f.status = RelationStatus.DECLINED
        await f.save()

        # TODO: Inform requesting user

    def get_all_relations(self, user: User) -> FindMany:
        # TODO: follow this discussion: https://github.com/roman-right/beanie/discussions/570
        return UserRelation.find(ElemMatch(UserRelation.users, {"$eq": user.id}))

    def get_all_active_relations(self, user: User) -> FindMany:
        fs = self.get_all_relations(user)
        return fs.find(UserRelation.status == RelationStatus.ACCEPTED)

    def get_active_and_open_relations(self, user: User) -> FindMany:
        fs = self.get_all_relations(user)
        filter = In(
            UserRelation.status, [RelationStatus.ACCEPTED, RelationStatus.PENDING]
        )
        return fs.find(filter)

    def get_open_relations(self, user: User) -> FindMany:
        fs = self.get_all_relations(user)
        return fs.find(UserRelation.status == RelationStatus.PENDING)

    async def get_received_requests(self, user: User) -> list[UserRelation]:
        fs = self.get_open_relations(user)
        pending = []
        async for f in fs:
            if f.users[1] != user.id:
                continue

            pending.append(f)

        return pending

    async def relations_to_users(
        self, user: User, relations: FindMany[UserRelation] | list[UserRelation]
    ):
        users = []

        async def _get(r):
            if user.id not in r.users:
                raise ValueError()
            id = r.users[1] if user.id == r.users[0] else r.users[0]

            u = await user_service.get_by_id(id)
            return u

        if isinstance(relations, FindMany):
            async for r in relations:
                users.append(await _get(r))
        else:  # list[UserRelations]
            for r in relations:
                users.append(await _get(r))

        return users

    async def has_relation_to(
        self, user_id_1: PydanticObjectId, user_id_2: PydanticObjectId
    ) -> UserRelation | None:
        f = await UserRelation.find_one(All(UserRelation.users, [user_id_1, user_id_2]))
        return f

    async def _create(self, ids, status):
        r = await UserRelation(
            users=ids,
            creation_date=datetime.utcnow(),
            status=status,
        ).insert()

        return r

    async def create_chatting(self, ids: list[PydanticObjectId]):
        r = await self._create(ids=ids, status=RelationStatus.CHATTING)
        return r


# global instances that can be imported by other modules
user_service = UserService()
relation_service = RelationService()
