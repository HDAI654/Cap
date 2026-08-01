class ApplicationError(Exception):
    """Base application error."""

    pass


class UnknownInstrumentError(ApplicationError):
    pass


class InvalidIncomingOrderError(ApplicationError):
    pass
