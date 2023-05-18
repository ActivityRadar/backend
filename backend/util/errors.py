
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
