class DomainError(Exception):
    """Base domain error."""


class InvalidUserIdError(DomainError):
    """User id is not a valid UUID v4."""


class InvalidSessionIdError(DomainError):
    """Session id is not a valid UUID v4."""



