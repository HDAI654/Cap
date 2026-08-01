from abc import ABC, abstractmethod
from decimal import Decimal

from src.domain.value_objects.instrument_id import InstrumentId


class MarketDataCache(ABC):
    """Outbound port for writing order-book snapshots and last trade price."""

    @abstractmethod
    async def write_last_trade_price(
        self,
        instrument_id: InstrumentId,
        price: Decimal,
        currency: str,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def write_book_snapshot(
        self,
        instrument_id: InstrumentId,
        bids: list[tuple[Decimal, int]],
        asks: list[tuple[Decimal, int]],
        last_trade_price: Decimal | None,
        last_trade_currency: str | None,
    ) -> None:
        raise NotImplementedError
