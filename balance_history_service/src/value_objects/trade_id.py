from shared.id_vo import ID
from src.exceptions import InvalidTradeIdError


class TradeId(ID):
    def __init__(self, value: str) -> None:
        super().__init__(value, InvalidTradeIdError)
