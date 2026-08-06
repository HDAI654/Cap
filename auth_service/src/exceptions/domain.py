class DomainError(Exception):
    """Base domain error."""

# ===== VOs =====
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

class InvalidDateError(DomainError):
    """Date value is invalid."""

class InvalidRoleError(DomainError):
    """Role value is not recognized."""

class InvalidEmailVerificationTokenError(DomainError):
    """Email verification token is not a valid UUID v4."""

class UserNotFoundError(DomainError):
    """User aggregate was not found."""

class UserAlreadyExistsError(DomainError):
    """User already exists for the given email."""
