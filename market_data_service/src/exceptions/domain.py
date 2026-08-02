class DomainError(Exception):
    """Base domain error."""

    pass


class InvalidInstrumentIdError(DomainError):
    pass
