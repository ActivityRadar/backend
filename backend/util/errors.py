
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
