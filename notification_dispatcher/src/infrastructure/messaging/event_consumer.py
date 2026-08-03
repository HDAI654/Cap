import json
import logging
from typing import Any

from src.application.dispatch_event import DispatchEventHandler
from src.exceptions import MessagingConnectionError, MessagingConsumeError

logger = logging.getLogger(__name__)

_TRADE_EVENTS = frozenset({"TradeExecuted", "OrderFilled", "OrderPlaced", "OrderRemoved"})
_ORDER_EVENTS = frozenset(
    {
        "OrderSubmitted",
        "OrderOpened",
        "OrderFilled",
        "OrderCancelled",
        "OrderRejected",
        "OrderExpired",
    }
)


class DispatcherEventConsumer:
    """Consume order/trade events and forward them to Notification Service."""

    def __init__(
        self,
        url: str,
        trade_exchange: str,
        order_exchange: str,
        queue_name: str,
        dispatch_handler: DispatchEventHandler,
        exchange_type: str = "topic",
        prefetch_count: int = 32,
    ) -> None:
        self._url = url
        self._trade_exchange = trade_exchange
        self._order_exchange = order_exchange
        self._queue_name = queue_name
        self._exchange_type = exchange_type
        self._prefetch_count = prefetch_count
        self._dispatch_handler = dispatch_handler
        self._connection = None
        self._channel = None

    async def start(self) -> None:
        try:
            import aio_pika
            from aio_pika import ExchangeType
        except ImportError as exc:
            raise MessagingConnectionError(
                "aio-pika is required. Install with: pip install aio-pika"
            ) from exc

        try:
            self._connection = await aio_pika.connect_robust(self._url)
            self._channel = await self._connection.channel()
            await self._channel.set_qos(prefetch_count=self._prefetch_count)

            trade_ex = await self._channel.declare_exchange(
                self._trade_exchange,
                ExchangeType(self._exchange_type),
                durable=True,
            )
            order_ex = await self._channel.declare_exchange(
                self._order_exchange,
                ExchangeType(self._exchange_type),
                durable=True,
            )
            queue = await self._channel.declare_queue(self._queue_name, durable=True)

            for key in _TRADE_EVENTS:
                await queue.bind(trade_ex, routing_key=key)
            for key in _ORDER_EVENTS:
                await queue.bind(order_ex, routing_key=key)

            await queue.consume(self._on_message)
            logger.info(
                "DispatcherEventConsumer started: queue=%s",
                self._queue_name,
            )
        except Exception as exc:
            logger.exception("Failed to start DispatcherEventConsumer")
            raise MessagingConnectionError(
                f"Failed to start dispatcher consumer: {exc}"
            ) from exc

    async def stop(self) -> None:
        if self._connection is not None and not self._connection.is_closed:
            await self._connection.close()
            logger.info("DispatcherEventConsumer stopped")
        self._connection = None
        self._channel = None

    async def _on_message(self, message: Any) -> None:
        async with message.process(requeue=False):
            try:
                payload = json.loads(message.body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                logger.error("Invalid message body: %s", exc)
                return

            event_type = payload.get("event_type") or message.routing_key
            try:
                await self._dispatch_handler.handle(str(event_type), payload)
            except Exception:
                logger.exception("Failed to dispatch event_type=%s", event_type)
                raise MessagingConsumeError(
                    f"Failed to dispatch event '{event_type}'"
                )
