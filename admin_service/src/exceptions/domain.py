class DomainError(Exception):
    """Base domain error."""

    pass


class InvalidInstrumentIdError(DomainError):
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


class InvalidInstrumentParametersError(DomainError):
    pass


class InvalidInstrumentStateError(DomainError):
    pass
