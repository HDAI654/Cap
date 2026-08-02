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
