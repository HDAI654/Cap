from unittest.mock import AsyncMock

from src.application.dispatch_event import DispatchEventHandler
from src.domain.ports.notification_gateway import NotificationGateway


async def test_dispatches_to_trader_id() -> None:
    gateway = AsyncMock(spec=NotificationGateway)
    gateway.push = AsyncMock()
    handler = DispatchEventHandler(gateway)

    await handler.handle(
        "OrderSubmitted",
        {
            "order_id": "o1",
            "trader_id": "t1",
            "instrument_id": "i1",
        },
    )

    gateway.push.assert_awaited_once()
    kwargs = gateway.push.await_args.kwargs
    assert kwargs["event_type"] == "OrderSubmitted"
    assert kwargs["recipient_trader_ids"] == ["t1"]
    assert kwargs["payload"]["order_id"] == "o1"


async def test_trade_notifies_buyer_and_seller() -> None:
    gateway = AsyncMock(spec=NotificationGateway)
    gateway.push = AsyncMock()
    handler = DispatchEventHandler(gateway)

    await handler.handle(
        "TradeExecuted",
        {
            "trade_id": "tr1",
            "buyer_id": "b1",
            "seller_id": "s1",
            "quantity": 5,
        },
    )

    kwargs = gateway.push.await_args.kwargs
    assert kwargs["recipient_trader_ids"] == ["b1", "s1"]


async def test_deduplicates_buyer_seller_same_id() -> None:
    gateway = AsyncMock(spec=NotificationGateway)
    gateway.push = AsyncMock()
    handler = DispatchEventHandler(gateway)

    await handler.handle(
        "TradeExecuted",
        {
            "trade_id": "tr1",
            "buyer_id": "same",
            "seller_id": "same",
        },
    )

    assert gateway.push.await_args.kwargs["recipient_trader_ids"] == ["same"]


async def test_no_recipients_skips_push() -> None:
    gateway = AsyncMock(spec=NotificationGateway)
    gateway.push = AsyncMock()
    handler = DispatchEventHandler(gateway)

    await handler.handle("OrderSubmitted", {"order_id": "o1"})

    gateway.push.assert_not_awaited()


async def test_ignores_empty_string_recipients() -> None:
    gateway = AsyncMock(spec=NotificationGateway)
    gateway.push = AsyncMock()
    handler = DispatchEventHandler(gateway)

    await handler.handle(
        "OrderSubmitted",
        {"trader_id": "", "order_id": "o1"},
    )

    gateway.push.assert_not_awaited()
