from shared.base_vo import BaseVO
from src.exceptions import InvalidQuantityError, QuantityOperationError


class Quantity(BaseVO[int]):
    """Represents the number of tradable shares."""

    def __init__(self, value: int):
        if not isinstance(value, int):
            raise InvalidQuantityError("Quantity must be an integer.")

        if value < 0:
            raise InvalidQuantityError("Quantity cannot be negative.")

        super().__init__(value)

    def __add__(self, other: "Quantity") -> "Quantity":
        self._validate_operand(other)
        return Quantity(self.value + other.value)

    def __sub__(self, other: "Quantity") -> "Quantity":
        self._validate_operand(other)

        result = self.value - other.value
        if result < 0:
            raise InvalidQuantityError("Quantity cannot become negative.")

        return Quantity(result)

    def __lt__(self, other: "Quantity") -> bool:
        self._validate_operand(other)
        return self.value < other.value

    def __le__(self, other: "Quantity") -> bool:
        self._validate_operand(other)
        return self.value <= other.value

    def __gt__(self, other: "Quantity") -> bool:
        self._validate_operand(other)
        return self.value > other.value

    def __ge__(self, other: "Quantity") -> bool:
        self._validate_operand(other)
        return self.value >= other.value

    def _validate_operand(other: object) -> None:
        """Validate that the operand is a Quantity."""
        if not isinstance(other, Quantity):
            raise QuantityOperationError(
                f"Expected Quantity, got {type(other).__name__}."
            )
