from shared.id_vo import ID
from src.exceptions import InvalidTradeIdError


class TradeId(ID):
    """Unique identifier of a trade."""

    def __init__(self, value: str) -> None:
        super().__init__(value, InvalidTradeIdError)
