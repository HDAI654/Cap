import logging
from dataclasses import dataclass

from src.domain.ports.market_data_reader import MarketDataReader
from src.domain.read_models.order_book_snapshot import OrderBookSnapshot
from src.domain.value_objects.instrument_id import InstrumentId
from src.exceptions import MarketDataNotFoundError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class GetOrderBookQuery:
    instrument_id: str


class GetOrderBookHandler:
    """Return the current order-book snapshot for an instrument."""

    def __init__(self, reader: MarketDataReader) -> None:
        self._reader = reader

    async def handle(self, query: GetOrderBookQuery) -> OrderBookSnapshot:
        logger.info("Getting order book: instrument_id=%s", query.instrument_id)
        instrument_id = InstrumentId(query.instrument_id)
        snapshot = await self._reader.get_order_book(instrument_id)
        if snapshot is None:
            raise MarketDataNotFoundError(
                f"No order book snapshot for instrument '{query.instrument_id}'."
            )
        return snapshot
