from decimal import Decimal

from shared.base_vo import BaseVO
from src.domain.value_objects.currency import Currency
from src.exceptions import (
    CurrencyMismatchError,
    InvalidCurrencyError,
    InvalidMoneyAmountError,
    MoneyOperationError,
)


class Money(BaseVO[Decimal]):
    """Monetary amount in a specific currency."""

    def __init__(self, amount: Decimal | int | str, currency: Currency) -> None:
        if not isinstance(currency, Currency):
            raise InvalidCurrencyError("Invalid currency.")
        try:
            decimal_amount = Decimal(amount)
        except Exception as exc:
            raise InvalidMoneyAmountError("Invalid monetary amount.") from exc
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
        return self.value

    @property
    def currency(self) -> Currency:
        return self._currency

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount == other.amount and self.currency is other.currency

    def __hash__(self) -> int:
        return hash((self.__class__, self.amount, self.currency))
