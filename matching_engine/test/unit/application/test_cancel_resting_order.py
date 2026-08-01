from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.application.cancel_resting_order import (
    CancelRestingOrderCommand,
    CancelRestingOrderHandler,
)
from src.application.process_incoming_order import (
    ProcessIncomingOrderCommand,
    ProcessIncomingOrderHandler,
)
from src.domain.events.matching_events import OrderRemoved
from src.domain.ports.order_book_registry import OrderBookRegistry
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.order_id import OrderId
from src.domain.value_objects.trader_id import TraderId
from src.exceptions import OrderNotInBookError


async def test_cancel_resting_order(
    registry: OrderBookRegistry,
    mock_event_publisher: AsyncMock,
    mock_cache: AsyncMock,
) -> None:
    process = ProcessIncomingOrderHandler(registry, mock_event_publisher, mock_cache)
    cancel = CancelRestingOrderHandler(registry, mock_event_publisher, mock_cache)

    order_id = OrderId.generate().value
    instrument_id = InstrumentId.generate().value

    await process.handle(
        ProcessIncomingOrderCommand(
            order_id=order_id,
            trader_id=TraderId.generate().value,
            instrument_id=instrument_id,
            side="BUY",
            order_type="LIMIT",
            time_in_force="GTC",
            quantity=3,
            limit_price=Decimal("1.00"),
            limit_price_currency="USD",
        )
    )
    mock_event_publisher.reset_mock()

    await cancel.handle(
        CancelRestingOrderCommand(order_id=order_id, instrument_id=instrument_id)
    )

    mock_event_publisher.publish.assert_awaited_once()
    event = mock_event_publisher.publish.await_args.args[0]
    assert isinstance(event, OrderRemoved)
    assert event.order_id == order_id
    assert event.remaining_quantity == 3


async def test_cancel_missing_order_raises(
    registry: OrderBookRegistry,
    mock_event_publisher: AsyncMock,
    mock_cache: AsyncMock,
) -> None:
    cancel = CancelRestingOrderHandler(registry, mock_event_publisher, mock_cache)

    with pytest.raises(OrderNotInBookError):
        await cancel.handle(
            CancelRestingOrderCommand(
                order_id=OrderId.generate().value,
                instrument_id=InstrumentId.generate().value,
            )
        )
