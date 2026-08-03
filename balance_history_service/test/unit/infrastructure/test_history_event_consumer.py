from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.exceptions import MessagingConsumeError
from src.infrastructure.messaging.history_event_consumer import HistoryEventConsumer


def _consumer(
    trade_handler: AsyncMock | None = None,
    order_handler: AsyncMock | None = None,
) -> HistoryEventConsumer:
    return HistoryEventConsumer(
        url="amqp://guest:guest@localhost:5672/",
        trade_exchange="trade.events",
        order_exchange="order.events",
        queue_name="balance_history.events",
        record_trade_handler=trade_handler or AsyncMock(),
        record_order_handler=order_handler or AsyncMock(),
    )


async def test_dispatch_trade_executed() -> None:
    trade_handler = AsyncMock()
    trade_handler.handle = AsyncMock()
    consumer = _consumer(trade_handler=trade_handler)

    await consumer._dispatch(
        "TradeExecuted",
        {
            "trade_id": "11111111-1111-4111-8111-111111111111",
            "maker_order_id": "22222222-2222-4222-8222-222222222222",
            "taker_order_id": "33333333-3333-4333-8333-333333333333",
            "buyer_id": "44444444-4444-4444-8444-444444444444",
            "seller_id": "55555555-5555-4555-8555-555555555555",
            "instrument_id": "66666666-6666-4666-8666-666666666666",
            "quantity": 5,
            "execution_price": "10.50",
            "execution_price_currency": "USD",
            "sequence_number": 2,
        },
    )

    trade_handler.handle.assert_awaited_once()
    command = trade_handler.handle.await_args.args[0]
    assert command.quantity == 5
    assert command.execution_price == Decimal("10.50")


async def test_dispatch_order_submitted() -> None:
    order_handler = AsyncMock()
    order_handler.handle = AsyncMock()
    consumer = _consumer(order_handler=order_handler)

    await consumer._dispatch(
        "OrderSubmitted",
        {
            "order_id": "11111111-1111-4111-8111-111111111111",
            "trader_id": "22222222-2222-4222-8222-222222222222",
            "instrument_id": "33333333-3333-4333-8333-333333333333",
            "side": "BUY",
            "order_type": "LIMIT",
            "quantity": 10,
            "limit_price": "1.25",
            "limit_price_currency": "USD",
        },
    )

    order_handler.handle.assert_awaited_once()
    command = order_handler.handle.await_args.args[0]
    assert command.event_type == "OrderSubmitted"
    assert command.price == Decimal("1.25")


async def test_dispatch_order_filled() -> None:
    order_handler = AsyncMock()
    order_handler.handle = AsyncMock()
    consumer = _consumer(order_handler=order_handler)

    await consumer._dispatch(
        "OrderFilled",
        {
            "order_id": "11111111-1111-4111-8111-111111111111",
            "trader_id": "22222222-2222-4222-8222-222222222222",
            "instrument_id": "33333333-3333-4333-8333-333333333333",
            "side": "BUY",
            "fill_quantity": 3,
            "remaining_quantity": 7,
            "status": "PARTIALLY_FILLED",
        },
    )

    command = order_handler.handle.await_args.args[0]
    assert command.event_type == "OrderFilled"
    assert command.filled_quantity == 3
    assert command.remaining_quantity == 7


async def test_dispatch_order_cancelled() -> None:
    order_handler = AsyncMock()
    order_handler.handle = AsyncMock()
    consumer = _consumer(order_handler=order_handler)

    await consumer._dispatch(
        "OrderCancelled",
        {
            "order_id": "11111111-1111-4111-8111-111111111111",
            "trader_id": "22222222-2222-4222-8222-222222222222",
            "instrument_id": "33333333-3333-4333-8333-333333333333",
            "side": "SELL",
            "filled_quantity": 0,
        },
    )

    assert order_handler.handle.await_args.args[0].event_type == "OrderCancelled"


async def test_trade_missing_price_raises() -> None:
    consumer = _consumer()
    with pytest.raises(MessagingConsumeError):
        await consumer._dispatch(
            "TradeExecuted",
            {
                "trade_id": "11111111-1111-4111-8111-111111111111",
                "maker_order_id": "22222222-2222-4222-8222-222222222222",
                "taker_order_id": "33333333-3333-4333-8333-333333333333",
                "buyer_id": "44444444-4444-4444-8444-444444444444",
                "seller_id": "55555555-5555-4555-8555-555555555555",
                "instrument_id": "66666666-6666-4666-8666-666666666666",
                "quantity": 1,
            },
        )


async def test_unknown_event_is_ignored() -> None:
    trade_handler = AsyncMock()
    trade_handler.handle = AsyncMock()
    order_handler = AsyncMock()
    order_handler.handle = AsyncMock()
    consumer = _consumer(trade_handler=trade_handler, order_handler=order_handler)

    await consumer._dispatch("SomethingElse", {"foo": "bar"})

    trade_handler.handle.assert_not_awaited()
    order_handler.handle.assert_not_awaited()
