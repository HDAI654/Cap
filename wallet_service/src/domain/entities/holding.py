from shared.entity import Entity
from src.exceptions import InvalidValueError
from wallet_service.src.domain.value_objects.instrument_id import InstrumentId
from wallet_service.src.domain.value_objects.money import Money
from wallet_service.src.domain.value_objects.quantity import Quantity


class Holding(Entity):
    """Represents the position of an instrument in a wallet."""

    def __init__(
        self,
        instrument_id: InstrumentId,
        available: Quantity,
        reserved: Quantity,
        average_cost: Money,
    ) -> None:
        self.instrument_id = instrument_id
        self.available = available
        self.reserved = reserved
        self.average_cost = average_cost

        super().__init__()

    def add(self, quantity: Quantity) -> None:
        """Increase the available quantity."""
        self.available += quantity

    def remove(self, quantity: Quantity) -> None:
        """Decrease the available quantity."""
        if self.available < quantity:
            raise InvalidValueError("Insufficient available quantity.")

        self.available -= quantity

    def reserve(self, quantity: Quantity) -> None:
        """Reserve shares."""
        if self.available < quantity:
            raise InvalidValueError("Insufficient available quantity.")

        self.available -= quantity
        self.reserved += quantity

    def release(self, quantity: Quantity) -> None:
        """Release reserved shares."""
        if self.reserved < quantity:
            raise InvalidValueError("Insufficient reserved quantity.")

        self.reserved -= quantity
        self.available += quantity

    def consume_reserved(self, quantity: Quantity) -> None:
        """Consume reserved shares permanently."""
        if self.reserved < quantity:
            raise InvalidValueError("Insufficient reserved quantity.")

        self.reserved -= quantity

    def update_average_cost(self, average_cost: Money) -> None:
        """Update the weighted average acquisition cost."""
        if average_cost.currency != self.average_cost.currency:
            raise InvalidValueError("Currency mismatch.")

        self.average_cost = average_cost
