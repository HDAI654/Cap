class DomainError(Exception):
    """Base domain error."""

    pass


# ===== VOs =====
class InvalidUserIdError(DomainError):
    """User id is not a valid UUID v4."""

    pass


class InvalidSessionIdError(DomainError):
    """Session id is not a valid UUID v4."""

    pass


class InvalidEmailError(DomainError):
    """Email format is invalid."""

    pass


class InvalidPasswordError(DomainError):
    """Password does not meet domain strength rules."""

    pass


class InvalidHashedPasswordError(DomainError):
    """Hashed password payload is invalid."""

    pass


class InvalidDeviceError(DomainError):
    """Device identifier is invalid."""

    pass


class InvalidDateError(DomainError):
    """Date value is invalid."""

    pass


class InvalidRoleError(DomainError):
    """Role value is not recognized."""

    pass


class InvalidEmailVerificationTokenError(DomainError):
    """Email verification token is not a valid UUID v4."""

    pass


class UserNotFoundError(DomainError):
    """User aggregate was not found."""

    pass


class UserAlreadyExistsError(DomainError):
    """User already exists for the given email."""

    pass


class SessionNotFoundError(DomainError):
    """Session was not found."""

    pass
