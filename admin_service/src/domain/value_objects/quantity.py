from shared.base_vo import BaseVO
from src.exceptions import InvalidQuantityError, QuantityOperationError


class Quantity(BaseVO[int]):
    """Number of shares."""

    def __init__(self, value: int) -> None:
        if not isinstance(value, int):
            raise InvalidQuantityError("Quantity must be an integer.")
        if value < 0:
            raise InvalidQuantityError("Quantity cannot be negative.")
        super().__init__(value)

    def __add__(self, other: "Quantity") -> "Quantity":
        if not isinstance(other, Quantity):
            raise QuantityOperationError(
                f"Expected Quantity, got {type(other).__name__}."
            )
        return Quantity(self.value + other.value)

    def __gt__(self, other: "Quantity") -> bool:
        if not isinstance(other, Quantity):
            raise QuantityOperationError(
                f"Expected Quantity, got {type(other).__name__}."
            )
        return self.value > other.value

    def __ge__(self, other: "Quantity") -> bool:
        if not isinstance(other, Quantity):
            raise QuantityOperationError(
                f"Expected Quantity, got {type(other).__name__}."
            )
        return self.value >= other.value
