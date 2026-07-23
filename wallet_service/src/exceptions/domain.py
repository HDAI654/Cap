class DomainError(Exception):
    """Base domain error"""

    pass


class InvalidValueError(DomainError):
    pass


class InvalidQuantityError(DomainError):
    """Raised when a Quantity value is invalid or malformed."""

    pass


class InvalidCurrencyError(DomainError):
    """Raised when a Currency value is invalid or malformed."""

    pass


class InvalidMoneyAmountError(DomainError):
    """Raised when a Money amount is invalid or malformed."""

    pass


class CurrencyMismatchError(DomainError):
    """Raised when money operations involve different currencies."""

    pass


class MoneyOperationError(DomainError):
    """Raised when a money operation receives an unsupported operand type."""

    pass


class QuantityOperationError(DomainError):
    """Raised when a quantity operation receives an unsupported operand type."""

    pass
