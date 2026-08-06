class ApplicationError(Exception):
    """Base application error."""

    pass

class EmailBlockedError(ApplicationError):
    """Email address is on the blocklist."""


