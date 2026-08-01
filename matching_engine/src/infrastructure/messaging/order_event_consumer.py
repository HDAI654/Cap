import json
import logging
from decimal import Decimal, InvalidOperation
from typing import Any

from src.application.cancel_resting_order import (
    CancelRestingOrderCommand,
    CancelRestingOrderHandler,
)
from src.application.process_incoming_order import (
    ProcessIncomingOrderCommand,
    ProcessIncomingOrderHandler,
)
from src.exceptions import MessagingConnectionError, MessagingConsumeError

logger = logging.getLogger(__name__)

# Routing keys consumed from order.events
_MATCH_EVENTS = frozenset({"OrderOpened"})
_CANCEL_EVENTS = frozenset({"OrderCancelled"})


class OrderEventConsumer:
    """Consumes OIS order lifecycle events and drives the matching engine.

    Binds a durable queue to the ``order.events`` topic exchange and dispatches:
      - OrderOpened  → ProcessIncomingOrderHandler
      - OrderCancelled → CancelRestingOrderHandler
    """

    def __init__(
        self,
        url: str,
        exchange_name: str,
        queue_name: str,
        process_handler: ProcessIncomingOrderHandler,
        cancel_handler: CancelRestingOrderHandler,
        exchange_type: str = "topic",
        prefetch_count: int = 32,
    ) -> None:
        self._url = url
        self._exchange_name = exchange_name
        self._queue_name = queue_name
        self._exchange_type = exchange_type
        self._prefetch_count = prefetch_count
        self._process_handler = process_handler
        self._cancel_handler = cancel_handler
        self._connection = None
        self._channel = None

    async def start(self) -> None:
        """Connect, declare topology, and begin consuming."""
        try:
            import aio_pika
            from aio_pika import ExchangeType
        except ImportError as exc:
            raise MessagingConnectionError(
                "aio-pika is required for OrderEventConsumer. "
                "Install it with: pip install aio-pika"
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
            queue = await self._channel.declare_queue(
                self._queue_name,
                durable=True,
            )
            for routing_key in _MATCH_EVENTS | _CANCEL_EVENTS:
                await queue.bind(exchange, routing_key=routing_key)

            await queue.consume(self._on_message)
            logger.info(
                "OrderEventConsumer started: queue=%s exchange=%s",
                self._queue_name,
                self._exchange_name,
            )
        except Exception as exc:
            logger.exception("Failed to start OrderEventConsumer")
            raise MessagingConnectionError(
                f"Failed to start order event consumer: {exc}"
            ) from exc

    async def stop(self) -> None:
        if self._connection is not None and not self._connection.is_closed:
            await self._connection.close()
            logger.info("OrderEventConsumer stopped")
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
                await self._dispatch(event_type, payload)
            except Exception:
                logger.exception(
                    "Failed to handle event_type=%s order_id=%s",
                    event_type,
                    payload.get("order_id"),
                )
                raise MessagingConsumeError(f"Failed to handle event '{event_type}'")

    async def _dispatch(self, event_type: str, payload: dict[str, Any]) -> None:
        if event_type in _MATCH_EVENTS:
            command = self._to_process_command(payload)
            await self._process_handler.handle(command)
        elif event_type in _CANCEL_EVENTS:
            command = CancelRestingOrderCommand(
                order_id=str(payload["order_id"]),
                instrument_id=str(payload["instrument_id"]),
            )
            await self._cancel_handler.handle(command)
        else:
            logger.debug("Ignoring unhandled event_type=%s", event_type)

    @staticmethod
    def _to_process_command(payload: dict[str, Any]) -> ProcessIncomingOrderCommand:
        limit_price: Decimal | None = None
        raw_price = payload.get("limit_price")
        if raw_price is not None and raw_price != "":
            try:
                limit_price = Decimal(str(raw_price))
            except (InvalidOperation, ValueError) as exc:
                raise MessagingConsumeError(
                    f"Invalid limit_price in event: {raw_price}"
                ) from exc

        quantity = payload.get("remaining_quantity", payload.get("quantity", 0))
        return ProcessIncomingOrderCommand(
            order_id=str(payload["order_id"]),
            trader_id=str(payload["trader_id"]),
            instrument_id=str(payload["instrument_id"]),
            side=str(payload["side"]),
            order_type=str(payload["order_type"]),
            time_in_force=str(payload.get("time_in_force") or "GTC"),
            quantity=int(quantity),
            limit_price=limit_price,
            limit_price_currency=payload.get("limit_price_currency"),
        )
