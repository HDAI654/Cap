import json
import logging
from typing import Any

from src.application.fill_order import FillOrderCommand, FillOrderHandler
from src.exceptions import MessagingConnectionError, MessagingConsumeError

logger = logging.getLogger(__name__)

_FILL_EVENTS = frozenset({"OrderFilled"})


class FillEventConsumer:
    """Apply Matching Engine fills back onto OIS order aggregates."""

    def __init__(
        self,
        url: str,
        exchange_name: str,
        queue_name: str,
        fill_handler: FillOrderHandler,
        exchange_type: str = "topic",
        prefetch_count: int = 32,
    ) -> None:
        self._url = url
        self._exchange_name = exchange_name
        self._queue_name = queue_name
        self._exchange_type = exchange_type
        self._prefetch_count = prefetch_count
        self._fill_handler = fill_handler
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

            exchange = await self._channel.declare_exchange(
                self._exchange_name,
                ExchangeType(self._exchange_type),
                durable=True,
            )
            queue = await self._channel.declare_queue(self._queue_name, durable=True)
            for key in _FILL_EVENTS:
                await queue.bind(exchange, routing_key=key)

            await queue.consume(self._on_message)
            logger.info("FillEventConsumer started: queue=%s", self._queue_name)
        except Exception as exc:
            logger.exception("Failed to start FillEventConsumer")
            raise MessagingConnectionError(
                f"Failed to start fill consumer: {exc}"
            ) from exc

    async def stop(self) -> None:
        if self._connection is not None and not self._connection.is_closed:
            await self._connection.close()
        self._connection = None
        self._channel = None

    async def _on_message(self, message: Any) -> None:
        async with message.process(requeue=False):
            try:
                payload = json.loads(message.body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                logger.error("Invalid fill message: %s", exc)
                return

            event_type = payload.get("event_type") or message.routing_key
            if event_type not in _FILL_EVENTS:
                return

            order_id = str(payload.get("order_id", ""))
            fill_qty = int(payload.get("fill_quantity") or 0)
            if not order_id or fill_qty <= 0:
                logger.warning("Ignoring fill with missing order_id/qty: %s", payload)
                return

            try:
                await self._fill_handler.handle(
                    FillOrderCommand(order_id=order_id, fill_quantity=fill_qty)
                )
            except Exception:
                logger.exception("Failed to apply fill order_id=%s", order_id)
                raise MessagingConsumeError(f"Failed to apply fill for '{order_id}'")
