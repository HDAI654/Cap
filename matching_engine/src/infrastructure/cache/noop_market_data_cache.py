import logging
from decimal import Decimal

from src.domain.ports.market_data_cache import MarketDataCache
from src.domain.value_objects.instrument_id import InstrumentId

logger = logging.getLogger(__name__)


class NoOpMarketDataCache(MarketDataCache):
    async def write_last_trade_price(
        self,
        instrument_id: InstrumentId,
        price: Decimal,
        currency: str,
    ) -> None:
        logger.debug(
            "NoOpMarketDataCache: LTP instrument=%s price=%s %s",
            instrument_id.value,
            price,
            currency,
        )

    async def write_book_snapshot(
        self,
        instrument_id: InstrumentId,
        bids: list[tuple[Decimal, int]],
        asks: list[tuple[Decimal, int]],
        last_trade_price: Decimal | None,
        last_trade_currency: str | None,
    ) -> None:
        logger.debug(
            "NoOpMarketDataCache: snapshot instrument=%s bids=%s asks=%s",
            instrument_id.value,
            len(bids),
            len(asks),
        )
