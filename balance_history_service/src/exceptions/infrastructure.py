class InfrastructureError(Exception):
    """Base infrastructure error."""

    pass


class DatabaseError(InfrastructureError):
    pass


class DatabaseConnectionError(DatabaseError):
    pass


class DatabaseTimeoutError(DatabaseError):
    pass


class DatabaseOperationError(DatabaseError):
    pass


class MessagingError(InfrastructureError):
    pass


class MessagingConnectionError(MessagingError):
    pass


class MessagingConsumeError(MessagingError):
    pass
