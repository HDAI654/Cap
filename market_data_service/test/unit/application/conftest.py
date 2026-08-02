from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.domain.ports.market_data_reader import MarketDataReader
from src.domain.read_models.order_book_snapshot import (
    LastTradePrice,
    OrderBookSnapshot,
    PriceLevel,
)
from src.domain.value_objects.instrument_id import InstrumentId


@pytest.fixture
def instrument_id() -> InstrumentId:
    return InstrumentId.generate()


@pytest.fixture
def sample_book(instrument_id: InstrumentId) -> OrderBookSnapshot:
    return OrderBookSnapshot(
        instrument_id=instrument_id.value,
        bids=(
            PriceLevel(price=Decimal("10.00"), quantity=100),
            PriceLevel(price=Decimal("9.50"), quantity=50),
        ),
        asks=(
            PriceLevel(price=Decimal("10.25"), quantity=80),
            PriceLevel(price=Decimal("10.50"), quantity=40),
        ),
        last_trade_price=Decimal("10.10"),
        last_trade_currency="USD",
    )


@pytest.fixture
def sample_ltp(instrument_id: InstrumentId) -> LastTradePrice:
    return LastTradePrice(
        instrument_id=instrument_id.value,
        price=Decimal("10.10"),
        currency="USD",
    )


@pytest.fixture
def mock_reader() -> AsyncMock:
    reader = AsyncMock(spec=MarketDataReader)
    reader.get_order_book = AsyncMock()
    reader.get_last_trade_price = AsyncMock()
    return reader
