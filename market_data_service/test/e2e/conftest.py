import os
from collections.abc import Iterator
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

os.environ["APP_ENV"] = "development"
os.environ["REDIS_ENABLED"] = "false"

from src.app import app  # noqa: E402
from src.domain.read_models.order_book_snapshot import (
    LastTradePrice,
    OrderBookSnapshot,
    PriceLevel,
)
from src.domain.value_objects.instrument_id import InstrumentId
from src.infrastructure.cache.in_memory_market_data_reader import (
    InMemoryMarketDataReader,
)


@pytest.fixture
def instrument_id() -> str:
    return InstrumentId.generate().value


@pytest.fixture
def client(instrument_id: str) -> Iterator[TestClient]:
    reader = InMemoryMarketDataReader()
    reader.seed_book(
        OrderBookSnapshot(
            instrument_id=instrument_id,
            bids=(
                PriceLevel(price=Decimal("100.00"), quantity=50),
                PriceLevel(price=Decimal("99.50"), quantity=20),
            ),
            asks=(PriceLevel(price=Decimal("100.50"), quantity=30),),
            last_trade_price=Decimal("100.25"),
            last_trade_currency="USD",
        )
    )
    reader.seed_ltp(
        LastTradePrice(
            instrument_id=instrument_id,
            price=Decimal("100.25"),
            currency="USD",
        )
    )
    app.state.market_data_reader = reader

    with TestClient(app) as test_client:
        yield test_client
