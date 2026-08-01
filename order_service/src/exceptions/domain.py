class DomainError(Exception):
    """Base domain error."""

    pass


# ======= VOs =======
class InvalidOrderIdError(DomainError):
    """Raised when an OrderId value is invalid or malformed."""

    pass


class InvalidTraderIdError(DomainError):
    """Raised when a TraderId value is invalid or malformed."""

    pass


class InvalidInstrumentIdError(DomainError):
    """Raised when an InstrumentId value is invalid or malformed."""

    pass
