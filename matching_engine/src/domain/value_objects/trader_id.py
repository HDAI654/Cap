from shared.id_vo import ID
from src.exceptions import InvalidTraderIdError


class TraderId(ID):
    """Unique identifier of a trader."""

    def __init__(self, value: str) -> None:
        super().__init__(value, InvalidTraderIdError)
