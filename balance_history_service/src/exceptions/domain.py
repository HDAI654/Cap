class DomainError(Exception):
    """Base domain error."""

    pass


class InvalidTradeIdError(DomainError):
    pass


class InvalidOrderIdError(DomainError):
    pass


class InvalidTraderIdError(DomainError):
    pass


class InvalidInstrumentIdError(DomainError):
    pass


class InvalidQuantityError(DomainError):
    pass


class InvalidMoneyAmountError(DomainError):
    pass
