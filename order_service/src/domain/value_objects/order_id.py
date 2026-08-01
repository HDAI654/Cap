from shared.id_vo import ID
from src.exceptions import InvalidOrderIdError


class OrderId(ID):
    """Represents the unique identifier of an Order aggregate."""

    def __init__(self, value: str) -> None:
        super().__init__(value, InvalidOrderIdError)
