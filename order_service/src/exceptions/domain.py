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


class InvalidIdempotencyKeyError(DomainError):
    """Raised when an IdempotencyKey value is invalid or malformed."""

    pass


# ======= Order Exceptions =======
class OrderException(DomainError):
    """Base Order error."""

    pass


class OrderNotFoundError(OrderException):
    """Order not found."""

    pass


class OrderDuplicateError(OrderException):
    """Order with same unique field exists."""

    pass


class InvalidOrderStateError(OrderException):
    """Order is not in a valid state for the requested operation."""

    pass


class InvalidOrderFillError(OrderException):
    """Fill quantity or price is invalid for the order."""

    pass


class InvalidOrderParametersError(OrderException):
    """Order creation parameters violate domain rules."""

    pass
