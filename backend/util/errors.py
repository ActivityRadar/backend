class UserDoesNotExist(Exception):
    ...


class UserLowTrust(Exception):
    ...


class UserWithNameExists(Exception):
    ...


class UserWrongPassword(Exception):
    ...


class UserNewPasswordIsOldPassword(Exception):
    ...


class UserNewPasswordDoesNotMatch(Exception):
    ...


class UserHasPendingRequest(Exception):
    ...


class UsernameAlreadyTaken(Exception):
    ...


class UserAlreadyLoggedOut(Exception):
    ...


class UserIsNotParticipant(Exception):
    ...


class UserAlreadyRequestedToJoin(Exception):
    ...


class ParticipantStatusUnchanged(Exception):
    ...


class EmailDoesNotMatchAccount(Exception):
    ...


class VerificationTimeout(Exception):
    ...


class AlreadyVerified(Exception):
    ...


class UserIsAlreadyArchived(Exception):
    def __init__(self, archived_until):
        self.archived_until = archived_until


class TokenInvalid(Exception):
    ...


class InvalidUpdateOption(Exception):
    def __init__(self, option: str) -> None:
        super().__init__()
        self.option = option


class RelationExists(Exception):
    def __init__(self, relation_id) -> None:
        super().__init__()
        self.id = relation_id


class RelationDoesNotExist(Exception):
    ...


class NotAnOpenRequest(Exception):
    def __init__(self, relation_id) -> None:
        super().__init__()
        self.id = relation_id


class UserIsNotPartOfRelation(Exception):
    def __init__(self, user_id, relation_id):
        super().__init__()
        self.user_id = user_id
        self.relation_id = relation_id


class UserCantReactToOwnRequest(Exception):
    ...


class UserCantSendAnotherRequestCurrently(Exception):
    ...


class UserHasReviewAlready(Exception):
    ...


class ReviewDoesNotExist(Exception):
    ...


class UserDoesNotOwnReview(Exception):
    ...


class UserHasAlreadyReportedThisReview(Exception):
    ...


class LocationDoesNotExist(Exception):
    ...


class InvalidUpdateType(Exception):
    ...


class InvalidHistory(Exception):
    ...


class InvalidBeforeData(Exception):
    ...


class TagExists(Exception):
    ...


class TagDoesNotExist(Exception):
    ...


class UserHasTooManyOngoingUpdateReports(Exception):
    ...


class OfferDoesNotExist(Exception):
    ...


class UserDoesNotOwnOffer(Exception):
    ...


class PhotoDoesNotExist(Exception):
    ...


class UserPostedTooManyPhotos(Exception):
    ...
