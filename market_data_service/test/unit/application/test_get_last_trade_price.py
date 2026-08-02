from unittest.mock import AsyncMock

import pytest

from src.application.get_last_trade_price import (
    GetLastTradePriceHandler,
    GetLastTradePriceQuery,
)
from src.domain.read_models.order_book_snapshot import LastTradePrice
from src.domain.value_objects.instrument_id import InstrumentId
from src.exceptions import MarketDataNotFoundError


async def test_returns_ltp(
    mock_reader: AsyncMock,
    instrument_id: InstrumentId,
    sample_ltp: LastTradePrice,
) -> None:
    mock_reader.get_last_trade_price.return_value = sample_ltp

    result = await GetLastTradePriceHandler(mock_reader).handle(
        GetLastTradePriceQuery(instrument_id=instrument_id.value)
    )

    assert result is sample_ltp
    mock_reader.get_last_trade_price.assert_awaited_once()


async def test_raises_when_missing(
    mock_reader: AsyncMock,
    instrument_id: InstrumentId,
) -> None:
    mock_reader.get_last_trade_price.return_value = None

    with pytest.raises(MarketDataNotFoundError):
        await GetLastTradePriceHandler(mock_reader).handle(
            GetLastTradePriceQuery(instrument_id=instrument_id.value)
        )
