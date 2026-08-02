import json
import logging
from decimal import Decimal, InvalidOperation

from src.domain.ports.market_data_reader import MarketDataReader
from src.domain.read_models.order_book_snapshot import (
    LastTradePrice,
    OrderBookSnapshot,
    PriceLevel,
)
from src.domain.value_objects.instrument_id import InstrumentId
from src.exceptions import CacheConnectionError, CacheOperationError

logger = logging.getLogger(__name__)

_BOOK_KEY = "md:book:{instrument_id}"
_LTP_KEY = "md:ltp:{instrument_id}"


class RedisMarketDataReader(MarketDataReader):
    """Reads order-book snapshots and LTP from Redis."""

    def __init__(self, url: str) -> None:
        self._url = url
        self._client = None

    async def connect(self) -> None:
        try:
            from redis.asyncio import Redis
        except ImportError as exc:
            raise CacheConnectionError(
                "redis is required for RedisMarketDataReader. "
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

    async def get_order_book(
        self,
        instrument_id: InstrumentId,
    ) -> OrderBookSnapshot | None:
        client = await self._ensure_client()
        key = _BOOK_KEY.format(instrument_id=instrument_id.value)
        try:
            raw = await client.get(key)
        except Exception as exc:
            logger.exception("Failed to read book key=%s", key)
            raise CacheOperationError(f"Failed to read order book: {exc}") from exc

        if raw is None:
            return None

        try:
            data = json.loads(raw)
            bids = tuple(
                PriceLevel(price=Decimal(str(p)), quantity=int(q))
                for p, q in data.get("bids", [])
            )
            asks = tuple(
                PriceLevel(price=Decimal(str(p)), quantity=int(q))
                for p, q in data.get("asks", [])
            )
            ltp_raw = data.get("last_trade_price")
            ltp = Decimal(str(ltp_raw)) if ltp_raw is not None else None
            return OrderBookSnapshot(
                instrument_id=data.get("instrument_id", instrument_id.value),
                bids=bids,
                asks=asks,
                last_trade_price=ltp,
                last_trade_currency=data.get("last_trade_currency"),
            )
        except (json.JSONDecodeError, InvalidOperation, TypeError, ValueError) as exc:
            logger.exception("Corrupt book snapshot key=%s", key)
            raise CacheOperationError(
                f"Corrupt order book snapshot for '{instrument_id.value}'."
            ) from exc

    async def get_last_trade_price(
        self,
        instrument_id: InstrumentId,
    ) -> LastTradePrice | None:
        client = await self._ensure_client()
        key = _LTP_KEY.format(instrument_id=instrument_id.value)
        try:
            raw = await client.get(key)
        except Exception as exc:
            logger.exception("Failed to read LTP key=%s", key)
            raise CacheOperationError(f"Failed to read LTP: {exc}") from exc

        if raw is None:
            return None

        try:
            data = json.loads(raw)
            return LastTradePrice(
                instrument_id=instrument_id.value,
                price=Decimal(str(data["price"])),
                currency=str(data["currency"]),
            )
        except (json.JSONDecodeError, KeyError, InvalidOperation, TypeError) as exc:
            logger.exception("Corrupt LTP key=%s", key)
            raise CacheOperationError(
                f"Corrupt last trade price for '{instrument_id.value}'."
            ) from exc

    async def _ensure_client(self):
        if self._client is None:
            await self.connect()
        return self._client
