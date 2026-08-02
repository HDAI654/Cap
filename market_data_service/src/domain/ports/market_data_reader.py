from abc import ABC, abstractmethod

from src.domain.read_models.order_book_snapshot import LastTradePrice, OrderBookSnapshot
from src.domain.value_objects.instrument_id import InstrumentId


class MarketDataReader(ABC):
    """Inbound cache port — reads snapshots written by the Matching Engine."""

    @abstractmethod
    async def get_order_book(
        self,
        instrument_id: InstrumentId,
    ) -> OrderBookSnapshot | None:
        raise NotImplementedError

    @abstractmethod
    async def get_last_trade_price(
        self,
        instrument_id: InstrumentId,
    ) -> LastTradePrice | None:
        raise NotImplementedError
