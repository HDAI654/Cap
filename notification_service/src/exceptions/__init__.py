class ApplicationError(Exception):
    """Base application error."""

    pass


class InvalidNotificationError(ApplicationError):
    pass
