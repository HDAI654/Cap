from shared.id_vo import ID
from src.exceptions import InvalidTraderIdError


class TraderId(ID):
    """Represents the unique identifier of a Trader."""

    def __init__(self, value: str) -> None:
        super().__init__(value, InvalidTraderIdError)
