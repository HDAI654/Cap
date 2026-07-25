from decimal import Decimal
from shared.base_vo import BaseVO
from src.exceptions import (
    InvalidCurrencyError,
    InvalidMoneyAmountError,
    CurrencyMismatchError,
    MoneyOperationError,
)
from src.domain.value_objects.currency import Currency


class Money(BaseVO[Decimal]):
    """Represents a monetary amount in a specific currency."""

    def __init__(self, amount: Decimal | int | str, currency: Currency):
        if not isinstance(currency, Currency):
            raise InvalidCurrencyError("Invalid currency.")

        try:
            decimal_amount = Decimal(amount)
        except Exception:
            raise InvalidMoneyAmountError("Invalid monetary amount.")

        if not decimal_amount.is_finite():
            raise InvalidMoneyAmountError("Monetary amount must be a finite number.")

        if decimal_amount < 0:
            raise InvalidMoneyAmountError("Monetary amount cannot be negative.")

        quantized = decimal_amount.quantize(Decimal("0.01"))
        if quantized != decimal_amount:
            raise InvalidMoneyAmountError("Amount must have at most 2 decimal places.")

        super().__init__(decimal_amount)

        self._currency = currency

    @property
    def amount(self) -> Decimal:
        """Return the monetary amount."""
        return self.value

    @property
    def currency(self) -> Currency:
        """Return the currency."""
        return self._currency

    def __add__(self, other: "Money") -> "Money":
        self._validate_operand("+", other)

        self._ensure_same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        self._validate_operand("-", other)

        self._ensure_same_currency(other)
        result = self.amount - other.amount
        if result < 0:
            raise InvalidMoneyAmountError("Monetary result cannot be negative")
        return Money(result, self.currency)

    def __lt__(self, other: "Money") -> bool:
        self._validate_operand("<", other)

        self._ensure_same_currency(other)
        return self.amount < other.amount

    def __le__(self, other: "Money") -> bool:
        self._validate_operand("<=", other)

        self._ensure_same_currency(other)
        return self.amount <= other.amount

    def __gt__(self, other: "Money") -> bool:
        self._validate_operand(">", other)

        self._ensure_same_currency(other)
        return self.amount > other.amount

    def __ge__(self, other: "Money") -> bool:
        self._validate_operand(">=", other)

        self._ensure_same_currency(other)
        return self.amount >= other.amount

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Money)
            and self.amount == other.amount
            and self.currency == other.currency
        )

    def __hash__(self) -> int:
        return hash((self.__class__, self.amount, self.currency))

    def _ensure_same_currency(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise CurrencyMismatchError(
                "Money operations require identical currencies."
            )

    def _validate_operand(self, operation: str, other: object) -> None:
        """Validate that the operand is a Money."""
        if not isinstance(other, Money):
            raise MoneyOperationError(
                f"unsupported operand type(s) for {operation}: 'Money' and '{type(other).__name__}'"
            )
