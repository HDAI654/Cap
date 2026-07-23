from shared.entity import Entity
from src.exceptions import InvalidValueError
from wallet_service.src.domain.value_objects.currency import Currency
from wallet_service.src.domain.value_objects.money import Money


class CashBalance(Entity):
    """Represents the cash balance for a specific currency."""

    def __init__(
        self,
        currency: Currency,
        available: Money,
        reserved: Money,
    ) -> None:
        if available.currency != currency:
            raise InvalidValueError("Available balance currency does not match.")

        if reserved.currency != currency:
            raise InvalidValueError("Reserved balance currency does not match.")

        self.currency = currency
        self.available = available
        self.reserved = reserved

        super().__init__()

    def deposit(self, amount: Money) -> None:
        """Increase the available balance."""
        self._validate_money(amount)
        self.available += amount

    def withdraw(self, amount: Money) -> None:
        """Decrease the available balance."""
        self._validate_money(amount)

        if self.available < amount:
            raise InvalidValueError("Insufficient available balance.")

        self.available -= amount

    def reserve(self, amount: Money) -> None:
        """Reserve funds from the available balance."""
        self._validate_money(amount)

        if self.available < amount:
            raise InvalidValueError("Insufficient available balance.")

        self.available -= amount
        self.reserved += amount

    def release(self, amount: Money) -> None:
        """Release reserved funds back to the available balance."""
        self._validate_money(amount)

        if self.reserved < amount:
            raise InvalidValueError("Insufficient reserved balance.")

        self.reserved -= amount
        self.available += amount

    def consume_reserved(self, amount: Money) -> None:
        """Consume reserved funds permanently."""
        self._validate_money(amount)

        if self.reserved < amount:
            raise InvalidValueError("Insufficient reserved balance.")

        self.reserved -= amount

    def _validate_money(self, amount: Money) -> None:
        if amount.currency != self.currency:
            raise InvalidValueError("Currency mismatch.")
