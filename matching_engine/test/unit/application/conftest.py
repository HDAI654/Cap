from unittest.mock import AsyncMock

import pytest

from src.domain.ports.event_publisher import EventPublisher
from src.domain.ports.market_data_cache import MarketDataCache
from src.domain.ports.order_book_registry import OrderBookRegistry
from src.infrastructure.book.in_memory_order_book_registry import (
    InMemoryOrderBookRegistry,
)


@pytest.fixture
def registry() -> OrderBookRegistry:
    return InMemoryOrderBookRegistry()


@pytest.fixture
def mock_event_publisher() -> AsyncMock:
    publisher = AsyncMock(spec=EventPublisher)
    publisher.publish = AsyncMock()
    return publisher


@pytest.fixture
def mock_cache() -> AsyncMock:
    cache = AsyncMock(spec=MarketDataCache)
    cache.write_last_trade_price = AsyncMock()
    cache.write_book_snapshot = AsyncMock()
    return cache
