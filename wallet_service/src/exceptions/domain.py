class DomainError(Exception):
    """Base domain error"""

    pass


class InvalidValueError(DomainError):
    pass
