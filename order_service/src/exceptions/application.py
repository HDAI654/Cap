class ApplicationError(Exception):
    """Base application error."""

    pass


class OrderAlreadyExistsError(ApplicationError):
    """Raised when an order already exists for the given idempotency key."""

    pass