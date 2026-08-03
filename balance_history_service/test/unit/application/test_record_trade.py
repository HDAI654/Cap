from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.application.record_trade import RecordTradeCommand, RecordTradeHandler
from src.exceptions import DuplicateTradeError


async def test_records_trade(
    mock_uow: AsyncMock,
    mock_trade_repo: AsyncMock,
) -> None:
    mock_trade_repo.exists.return_value = False

    await RecordTradeHandler(mock_uow).handle(
        RecordTradeCommand(
            trade_id="11111111-1111-4111-8111-111111111111",
            maker_order_id="22222222-2222-4222-8222-222222222222",
            taker_order_id="33333333-3333-4333-8333-333333333333",
            buyer_id="44444444-4444-4444-8444-444444444444",
            seller_id="55555555-5555-4555-8555-555555555555",
            instrument_id="66666666-6666-4666-8666-666666666666",
            quantity=5,
            execution_price=Decimal("10.00"),
            execution_price_currency="USD",
            sequence_number=1,
        )
    )

    mock_trade_repo.add.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


async def test_duplicate_trade_raises(
    mock_uow: AsyncMock,
    mock_trade_repo: AsyncMock,
) -> None:
    mock_trade_repo.exists.return_value = True

    with pytest.raises(DuplicateTradeError):
        await RecordTradeHandler(mock_uow).handle(
            RecordTradeCommand(
                trade_id="11111111-1111-4111-8111-111111111111",
                maker_order_id="22222222-2222-4222-8222-222222222222",
                taker_order_id="33333333-3333-4333-8333-333333333333",
                buyer_id="44444444-4444-4444-8444-444444444444",
                seller_id="55555555-5555-4555-8555-555555555555",
                instrument_id="66666666-6666-4666-8666-666666666666",
                quantity=5,
                execution_price=Decimal("10.00"),
                execution_price_currency="USD",
                sequence_number=1,
            )
        )

    mock_trade_repo.add.assert_not_awaited()
