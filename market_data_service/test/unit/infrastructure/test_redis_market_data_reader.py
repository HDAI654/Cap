import json
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.value_objects.instrument_id import InstrumentId
from src.exceptions import CacheConnectionError, CacheOperationError
from src.infrastructure.cache.redis_market_data_reader import RedisMarketDataReader


def _reader_with_client(client: AsyncMock) -> RedisMarketDataReader:
    reader = RedisMarketDataReader(url="redis://localhost:6379/0")
    reader._client = client
    return reader


async def test_get_order_book_parses_snapshot() -> None:
    instrument_id = InstrumentId.generate()
    payload = {
        "instrument_id": instrument_id.value,
        "bids": [["10.00", 100], ["9.50", 50]],
        "asks": [["10.25", 80]],
        "last_trade_price": "10.10",
        "last_trade_currency": "USD",
    }
    client = AsyncMock()
    client.get = AsyncMock(return_value=json.dumps(payload))
    reader = _reader_with_client(client)

    snapshot = await reader.get_order_book(instrument_id)

    assert snapshot is not None
    assert snapshot.instrument_id == instrument_id.value
    assert len(snapshot.bids) == 2
    assert snapshot.bids[0].price == Decimal("10.00")
    assert snapshot.bids[0].quantity == 100
    assert snapshot.asks[0].price == Decimal("10.25")
    assert snapshot.last_trade_price == Decimal("10.10")
    assert snapshot.last_trade_currency == "USD"
    client.get.assert_awaited_once_with(f"md:book:{instrument_id.value}")


async def test_get_order_book_returns_none_when_missing() -> None:
    client = AsyncMock()
    client.get = AsyncMock(return_value=None)
    reader = _reader_with_client(client)

    result = await reader.get_order_book(InstrumentId.generate())

    assert result is None


async def test_get_order_book_raises_on_corrupt_json() -> None:
    client = AsyncMock()
    client.get = AsyncMock(return_value="not-json")
    reader = _reader_with_client(client)

    with pytest.raises(CacheOperationError):
        await reader.get_order_book(InstrumentId.generate())


async def test_get_order_book_raises_on_redis_error() -> None:
    client = AsyncMock()
    client.get = AsyncMock(side_effect=RuntimeError("redis down"))
    reader = _reader_with_client(client)

    with pytest.raises(CacheOperationError):
        await reader.get_order_book(InstrumentId.generate())


async def test_get_ltp_parses_payload() -> None:
    instrument_id = InstrumentId.generate()
    payload = {"price": "42.50", "currency": "USD"}
    client = AsyncMock()
    client.get = AsyncMock(return_value=json.dumps(payload))
    reader = _reader_with_client(client)

    ltp = await reader.get_last_trade_price(instrument_id)

    assert ltp is not None
    assert ltp.price == Decimal("42.50")
    assert ltp.currency == "USD"
    client.get.assert_awaited_once_with(f"md:ltp:{instrument_id.value}")


async def test_get_ltp_returns_none_when_missing() -> None:
    client = AsyncMock()
    client.get = AsyncMock(return_value=None)
    reader = _reader_with_client(client)

    assert await reader.get_last_trade_price(InstrumentId.generate()) is None


async def test_get_ltp_raises_on_corrupt_payload() -> None:
    client = AsyncMock()
    client.get = AsyncMock(return_value=json.dumps({"price": "x"}))
    reader = _reader_with_client(client)

    with pytest.raises(CacheOperationError):
        await reader.get_last_trade_price(InstrumentId.generate())


async def test_connect_raises_when_redis_package_missing() -> None:
    reader = RedisMarketDataReader(url="redis://localhost:6379/0")

    with patch.dict("sys.modules", {"redis": None, "redis.asyncio": None}):
        with patch(
            "builtins.__import__",
            side_effect=ImportError("No module named redis"),
        ):
            with pytest.raises(CacheConnectionError):
                await reader.connect()
