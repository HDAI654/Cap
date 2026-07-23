class DomainError(Exception):
    """Base domain error"""

    pass


# ======= VOs =======
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


# ======= # CashBalance Exceptions =======
class CashBalanceException(DomainError):
    """Base CashBalance error"""

    pass


class CashBalanceNotFoundError(CashBalanceException):
    """CashBalance not found"""

    pass


class CashBalanceDuplicateError(CashBalanceException):
    """CashBalance with same unique field exists"""

    pass


# ======= # Holding Exceptions =======
class HoldingException(DomainError):
    """Base Holding error"""

    pass


class HoldingNotFoundError(HoldingException):
    """Holding not found"""

    pass


class HoldingDuplicateError(HoldingException):
    """Holding with same unique field exists"""

    pass
