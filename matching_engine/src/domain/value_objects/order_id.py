from shared.id_vo import ID
from src.exceptions import InvalidOrderIdError


class OrderId(ID):
    """Unique identifier of an order."""

    def __init__(self, value: str) -> None:
        super().__init__(value, InvalidOrderIdError)
