class DomainError(Exception):
    """Base domain error."""

    pass


class InvalidOrderIdError(DomainError):
    pass


class InvalidTraderIdError(DomainError):
    pass


class InvalidInstrumentIdError(DomainError):
    pass


class InvalidTradeIdError(DomainError):
    pass


class InvalidQuantityError(DomainError):
    pass


class QuantityOperationError(DomainError):
    pass


class InvalidCurrencyError(DomainError):
    pass


class InvalidMoneyAmountError(DomainError):
    pass


class CurrencyMismatchError(DomainError):
    pass


class MoneyOperationError(DomainError):
    pass


class InvalidOrderBookError(DomainError):
    pass


class OrderNotInBookError(DomainError):
    pass


class SelfTradeError(DomainError):
    pass
