class DomainError(Exception):
    """Base domain error."""


class InvalidUserIdError(DomainError):
    """User id is not a valid UUID v4."""


class InvalidSessionIdError(DomainError):
    """Session id is not a valid UUID v4."""

class InvalidEmailError(DomainError):
    """Email format is invalid."""


class InvalidPasswordError(DomainError):
    """Password does not meet domain strength rules."""

class InvalidHashedPasswordError(DomainError):
    """Hashed password payload is invalid."""

class InvalidDeviceError(DomainError):
    """Device identifier is invalid."""


