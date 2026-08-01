from decimal import Decimal
from unittest.mock import AsyncMock

from src.application.process_incoming_order import (
    ProcessIncomingOrderCommand,
    ProcessIncomingOrderHandler,
)
from src.domain.events.matching_events import OrderFilled, OrderPlaced, TradeExecuted
from src.domain.ports.order_book_registry import OrderBookRegistry
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.order_id import OrderId
from src.domain.value_objects.trader_id import TraderId


async def test_rests_limit_order_on_empty_book(
    registry: OrderBookRegistry,
    mock_event_publisher: AsyncMock,
    mock_cache: AsyncMock,
) -> None:
    handler = ProcessIncomingOrderHandler(registry, mock_event_publisher, mock_cache)
    order_id = OrderId.generate().value
    instrument_id = InstrumentId.generate().value

    result = await handler.handle(
        ProcessIncomingOrderCommand(
            order_id=order_id,
            trader_id=TraderId.generate().value,
            instrument_id=instrument_id,
            side="BUY",
            order_type="LIMIT",
            time_in_force="GTC",
            quantity=10,
            limit_price=Decimal("10.50"),
            limit_price_currency="USD",
        )
    )

    assert result.trades == ()
    assert result.resting_order is not None
    mock_event_publisher.publish.assert_awaited()
    event_types = [
        c.args[0].event_type for c in mock_event_publisher.publish.await_args_list
    ]
    assert "OrderPlaced" in event_types
    assert "TradeExecuted" not in event_types
    mock_cache.write_book_snapshot.assert_awaited()


async def test_matches_and_publishes_trade(
    registry: OrderBookRegistry,
    mock_event_publisher: AsyncMock,
    mock_cache: AsyncMock,
) -> None:
    handler = ProcessIncomingOrderHandler(registry, mock_event_publisher, mock_cache)
    instrument_id = InstrumentId.generate().value
    seller = TraderId.generate().value
    buyer = TraderId.generate().value

    await handler.handle(
        ProcessIncomingOrderCommand(
            order_id=OrderId.generate().value,
            trader_id=seller,
            instrument_id=instrument_id,
            side="SELL",
            order_type="LIMIT",
            time_in_force="GTC",
            quantity=5,
            limit_price=Decimal("10.00"),
            limit_price_currency="USD",
        )
    )
    mock_event_publisher.reset_mock()
    mock_cache.reset_mock()

    result = await handler.handle(
        ProcessIncomingOrderCommand(
            order_id=OrderId.generate().value,
            trader_id=buyer,
            instrument_id=instrument_id,
            side="BUY",
            order_type="LIMIT",
            time_in_force="GTC",
            quantity=5,
            limit_price=Decimal("10.00"),
            limit_price_currency="USD",
        )
    )

    assert len(result.trades) == 1
    assert result.taker_fully_filled is True

    published = [c.args[0] for c in mock_event_publisher.publish.await_args_list]
    types = {e.event_type for e in published}
    assert "TradeExecuted" in types
    assert "OrderFilled" in types
    trade_events = [e for e in published if isinstance(e, TradeExecuted)]
    assert trade_events[0].quantity == 5
    assert trade_events[0].execution_price == Decimal("10.00")
    mock_cache.write_last_trade_price.assert_awaited()
