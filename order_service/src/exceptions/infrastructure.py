class InfrastructureError(Exception):
    """Base infrastructure error."""

    pass


# ======= DB =======
class DatabaseError(InfrastructureError):
    """Base exception for database errors."""

    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when cannot connect to database."""

    pass


class DatabaseTimeoutError(DatabaseError):
    """Raised when database operation times out."""

    pass


class DatabaseOperationError(DatabaseError):
    """Raised when database operation fails."""

    pass


# ======= Messaging =======
class MessagingError(InfrastructureError):
    """Base exception for event-bus messaging errors."""

    pass


class MessagingConnectionError(MessagingError):
    """Raised when cannot connect to the event bus."""

    pass


class MessagingPublishError(MessagingError):
    """Raised when publishing an event fails."""

    pass
