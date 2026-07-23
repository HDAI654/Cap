from decimal import Decimal
from shared.base_vo import BaseVO
from shared.exceptions import InvalidValueError
from wallet_service.src.domain.value_objects.currency import Currency


class Money(BaseVO[Decimal]):
    """Represents a monetary amount in a specific currency."""

    def __init__(self, amount: Decimal | int | str, currency: Currency):
        if not isinstance(currency, Currency):
            raise InvalidValueError("Invalid currency.")

        try:
            decimal_amount = Decimal(amount)
        except Exception as exc:
            raise InvalidValueError("Invalid monetary amount.") from exc

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

    def __add__(self, other: Money) -> Money:
        self._ensure_same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        self._ensure_same_currency(other)
        return Money(self.amount - other.amount, self.currency)

    def __lt__(self, other: Money) -> bool:
        self._ensure_same_currency(other)
        return self.amount < other.amount

    def __le__(self, other: Money) -> bool:
        self._ensure_same_currency(other)
        return self.amount <= other.amount

    def __gt__(self, other: Money) -> bool:
        self._ensure_same_currency(other)
        return self.amount > other.amount

    def __ge__(self, other: Money) -> bool:
        self._ensure_same_currency(other)
        return self.amount >= other.amount

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return False

        return self.amount == other.amount and self.currency == other.currency

    def __hash__(self) -> int:
        return hash((self.amount, self.currency))

    def _ensure_same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise InvalidValueError("Money operations require identical currencies.")
