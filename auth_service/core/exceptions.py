class AuthenticationFailed(Exception):
    """Raised when authentication fails due to invalid credentials."""

    pass


class UserAlreadyExists(Exception):
    """Raised when trying to create a user that already exists."""

    pass


class InvalidTokenError(Exception):
    """Raised when the token is invalid."""

    pass


class SessionDoesNotExist(Exception):
    """Raised when the session does not exist."""

    pass


class NoSessionFound(Exception):
    """Raised when the no session found."""

    pass


class InfrastructureError(Exception):
    """Base class for infrastructure failures."""


class CacheError(InfrastructureError):
    """Redis / cache failure."""


class SessionStorageError(CacheError):
    """Failed to read/write/delete session in cache."""
