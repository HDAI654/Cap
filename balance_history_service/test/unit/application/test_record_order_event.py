from unittest.mock import AsyncMock

from src.application.record_order_event import (
    RecordOrderEventCommand,
    RecordOrderEventHandler,
)
from src.domain.entities.order_history_entry import OrderHistoryEntry


async def test_records_order_event(
    mock_uow: AsyncMock,
    mock_order_history_repo: AsyncMock,
) -> None:
    await RecordOrderEventHandler(mock_uow).handle(
        RecordOrderEventCommand(
            order_id="11111111-1111-4111-8111-111111111111",
            trader_id="22222222-2222-4222-8222-222222222222",
            instrument_id="33333333-3333-4333-8333-333333333333",
            event_type="OrderSubmitted",
            side="BUY",
            order_type="LIMIT",
            quantity=10,
        )
    )

    mock_order_history_repo.add.assert_awaited_once()
    entry: OrderHistoryEntry = mock_order_history_repo.add.await_args.args[0]
    assert entry.event_type == "OrderSubmitted"
    assert entry.order_id == "11111111-1111-4111-8111-111111111111"
    mock_uow.commit.assert_awaited_once()
