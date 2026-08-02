import logging
from dataclasses import dataclass

from src.domain.ports.market_data_reader import MarketDataReader
from src.domain.read_models.order_book_snapshot import LastTradePrice
from src.domain.value_objects.instrument_id import InstrumentId
from src.exceptions import MarketDataNotFoundError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class GetLastTradePriceQuery:
    instrument_id: str


class GetLastTradePriceHandler:
    """Return the last trade price for an instrument."""

    def __init__(self, reader: MarketDataReader) -> None:
        self._reader = reader

    async def handle(self, query: GetLastTradePriceQuery) -> LastTradePrice:
        logger.info("Getting LTP: instrument_id=%s", query.instrument_id)
        instrument_id = InstrumentId(query.instrument_id)
        ltp = await self._reader.get_last_trade_price(instrument_id)
        if ltp is None:
            raise MarketDataNotFoundError(
                f"No last trade price for instrument '{query.instrument_id}'."
            )
        return ltp
