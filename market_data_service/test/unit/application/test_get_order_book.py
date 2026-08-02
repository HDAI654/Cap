from unittest.mock import AsyncMock

import pytest

from src.application.get_order_book import GetOrderBookHandler, GetOrderBookQuery
from src.domain.read_models.order_book_snapshot import OrderBookSnapshot
from src.domain.value_objects.instrument_id import InstrumentId
from src.exceptions import MarketDataNotFoundError


async def test_returns_snapshot(
    mock_reader: AsyncMock,
    instrument_id: InstrumentId,
    sample_book: OrderBookSnapshot,
) -> None:
    mock_reader.get_order_book.return_value = sample_book

    result = await GetOrderBookHandler(mock_reader).handle(
        GetOrderBookQuery(instrument_id=instrument_id.value)
    )

    assert result is sample_book
    mock_reader.get_order_book.assert_awaited_once()


async def test_raises_when_missing(
    mock_reader: AsyncMock,
    instrument_id: InstrumentId,
) -> None:
    mock_reader.get_order_book.return_value = None

    with pytest.raises(MarketDataNotFoundError):
        await GetOrderBookHandler(mock_reader).handle(
            GetOrderBookQuery(instrument_id=instrument_id.value)
        )
