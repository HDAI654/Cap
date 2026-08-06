class ApplicationError(Exception):
    """Base application error."""

    pass

class EmailBlockedError(ApplicationError):
    """Email address is on the blocklist."""

class InvalidEmailOrPasswordError(ApplicationError):
    """Login failed (generic message — do not leak which field failed)."""


class InvalidVerificationTokenError(ApplicationError):
    """Verification or reset token is missing or expired."""


