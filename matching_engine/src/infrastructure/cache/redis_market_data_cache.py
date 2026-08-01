import json
import logging
from decimal import Decimal

from src.domain.ports.market_data_cache import MarketDataCache
from src.domain.value_objects.instrument_id import InstrumentId
from src.exceptions import CacheConnectionError, CacheOperationError

logger = logging.getLogger(__name__)


class RedisMarketDataCache(MarketDataCache):
    """Writes last-trade price and book snapshots to Redis.

    Keys:
      - ``md:ltp:{instrument_id}`` → JSON ``{price, currency}``
      - ``md:book:{instrument_id}`` → JSON snapshot
    """

    def __init__(self, url: str) -> None:
        self._url = url
        self._client = None

    async def connect(self) -> None:
        try:
            from redis.asyncio import Redis
        except ImportError as exc:
            raise CacheConnectionError(
                "redis is required for RedisMarketDataCache. "
                "Install it with: pip install redis"
            ) from exc

        try:
            self._client = Redis.from_url(self._url, decode_responses=True)
            await self._client.ping()
            logger.info("Connected to Redis: %s", self._url)
        except Exception as exc:
            logger.exception("Failed to connect to Redis")
            raise CacheConnectionError(f"Failed to connect to Redis: {exc}") from exc

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.info("Redis connection closed")

    async def write_last_trade_price(
        self,
        instrument_id: InstrumentId,
        price: Decimal,
        currency: str,
    ) -> None:
        client = await self._ensure_client()
        key = f"md:ltp:{instrument_id.value}"
        payload = json.dumps({"price": str(price), "currency": currency})
        try:
            await client.set(key, payload)
        except Exception as exc:
            logger.exception("Failed to write LTP key=%s", key)
            raise CacheOperationError(f"Failed to write LTP: {exc}") from exc

    async def write_book_snapshot(
        self,
        instrument_id: InstrumentId,
        bids: list[tuple[Decimal, int]],
        asks: list[tuple[Decimal, int]],
        last_trade_price: Decimal | None,
        last_trade_currency: str | None,
    ) -> None:
        client = await self._ensure_client()
        key = f"md:book:{instrument_id.value}"
        payload = json.dumps(
            {
                "instrument_id": instrument_id.value,
                "bids": [[str(p), q] for p, q in bids],
                "asks": [[str(p), q] for p, q in asks],
                "last_trade_price": (
                    str(last_trade_price) if last_trade_price is not None else None
                ),
                "last_trade_currency": last_trade_currency,
            }
        )
        try:
            await client.set(key, payload)
        except Exception as exc:
            logger.exception("Failed to write book snapshot key=%s", key)
            raise CacheOperationError(f"Failed to write book snapshot: {exc}") from exc

    async def _ensure_client(self):
        if self._client is None:
            await self.connect()
        return self._client
