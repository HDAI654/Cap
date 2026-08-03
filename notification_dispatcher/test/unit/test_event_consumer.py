from unittest.mock import AsyncMock

from src.application.dispatch_event import DispatchEventHandler
from src.infrastructure.messaging.event_consumer import DispatcherEventConsumer


class _ProcessCtx:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None


def _consumer(handler: DispatchEventHandler) -> DispatcherEventConsumer:
    return DispatcherEventConsumer(
        url="amqp://guest:guest@localhost:5672/",
        trade_exchange="trade.events",
        order_exchange="order.events",
        queue_name="notification_dispatcher.events",
        dispatch_handler=handler,
    )


async def test_on_message_dispatches_parsed_payload() -> None:
    gateway = AsyncMock()
    gateway.push = AsyncMock()
    handler = DispatchEventHandler(gateway)
    consumer = _consumer(handler)

    message = AsyncMock()
    message.body = b'{"event_type":"OrderCancelled","trader_id":"t1","order_id":"o1"}'
    message.routing_key = "OrderCancelled"
    message.process = lambda requeue=False: _ProcessCtx()

    await consumer._on_message(message)

    gateway.push.assert_awaited_once()
    assert gateway.push.await_args.kwargs["event_type"] == "OrderCancelled"
    assert gateway.push.await_args.kwargs["recipient_trader_ids"] == ["t1"]


async def test_on_message_ignores_invalid_json() -> None:
    gateway = AsyncMock()
    gateway.push = AsyncMock()
    handler = DispatchEventHandler(gateway)
    consumer = _consumer(handler)

    message = AsyncMock()
    message.body = b"not-json"
    message.routing_key = "OrderCancelled"
    message.process = lambda requeue=False: _ProcessCtx()

    await consumer._on_message(message)

    gateway.push.assert_not_awaited()
