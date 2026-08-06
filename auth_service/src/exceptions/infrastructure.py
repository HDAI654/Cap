class InfrastructureError(Exception):
    """Base infrastructure error."""


class DatabaseError(InfrastructureError):
    """Database operation failed."""


class CacheError(InfrastructureError):
    """Cache operation failed."""


class CacheConnectionError(CacheError):
    """Failed to connect to the cache."""


class CacheTimeoutError(CacheError):
    """Cache operation timed out."""


class CacheOperationError(CacheError):
    """Generic cache operation failure."""


class MessagingError(InfrastructureError):
    """Event bus operation failed."""


class TokenInfrastructureError(InfrastructureError):
    """Token encode/decode infrastructure failure."""


class DatabaseConnectionError(DatabaseError):
    """Failed to connect to the database."""


class DatabaseOperationError(DatabaseError):
    """A database operation failed."""


class DatabaseTimeoutError(DatabaseError):
    """A database operation timed out."""
