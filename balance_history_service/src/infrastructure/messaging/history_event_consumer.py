import json
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from src.application.record_order_event import (
    RecordOrderEventCommand,
    RecordOrderEventHandler,
)
from src.application.record_trade import RecordTradeCommand, RecordTradeHandler
from src.exceptions import DuplicateTradeError, MessagingConnectionError, MessagingConsumeError

logger = logging.getLogger(__name__)

_TRADE_EVENTS = frozenset({"TradeExecuted"})
_ORDER_EVENTS = frozenset(
    {
        "OrderSubmitted",
        "OrderOpened",
        "OrderFilled",
        "OrderCancelled",
        "OrderRejected",
        "OrderExpired",
        "OrderPlaced",
        "OrderRemoved",
    }
)


class HistoryEventConsumer:
    """Consumes trade.events and order.events and projects history rows."""

    def __init__(
        self,
        url: str,
        trade_exchange: str,
        order_exchange: str,
        queue_name: str,
        record_trade_handler: RecordTradeHandler,
        record_order_handler: RecordOrderEventHandler,
        exchange_type: str = "topic",
        prefetch_count: int = 32,
    ) -> None:
        self._url = url
        self._trade_exchange = trade_exchange
        self._order_exchange = order_exchange
        self._queue_name = queue_name
        self._exchange_type = exchange_type
        self._prefetch_count = prefetch_count
        self._record_trade = record_trade_handler
        self._record_order = record_order_handler
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
                "HistoryEventConsumer started: queue=%s",
                self._queue_name,
            )
        except Exception as exc:
            logger.exception("Failed to start HistoryEventConsumer")
            raise MessagingConnectionError(
                f"Failed to start history consumer: {exc}"
            ) from exc

    async def stop(self) -> None:
        if self._connection is not None and not self._connection.is_closed:
            await self._connection.close()
            logger.info("HistoryEventConsumer stopped")
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
            except DuplicateTradeError:
                logger.info(
                    "Skipping duplicate trade: trade_id=%s",
                    payload.get("trade_id"),
                )
            except Exception:
                logger.exception("Failed to handle event_type=%s", event_type)
                raise MessagingConsumeError(f"Failed to handle event '{event_type}'")

    async def _dispatch(self, event_type: str, payload: dict[str, Any]) -> None:
        if event_type in _TRADE_EVENTS:
            await self._record_trade.handle(self._to_trade_command(payload))
        elif event_type in _ORDER_EVENTS:
            await self._record_order.handle(
                self._to_order_command(event_type, payload)
            )
        else:
            logger.debug("Ignoring event_type=%s", event_type)

    @staticmethod
    def _to_trade_command(payload: dict[str, Any]) -> RecordTradeCommand:
        price_raw = payload.get("execution_price")
        if price_raw is None:
            raise MessagingConsumeError("TradeExecuted missing execution_price")
        try:
            price = Decimal(str(price_raw))
        except (InvalidOperation, ValueError) as exc:
            raise MessagingConsumeError("Invalid execution_price") from exc

        occurred = payload.get("occurred_at")
        executed_at = None
        if occurred:
            executed_at = datetime.fromisoformat(str(occurred).replace("Z", "+00:00"))

        return RecordTradeCommand(
            trade_id=str(payload["trade_id"]),
            maker_order_id=str(payload["maker_order_id"]),
            taker_order_id=str(payload["taker_order_id"]),
            buyer_id=str(payload["buyer_id"]),
            seller_id=str(payload["seller_id"]),
            instrument_id=str(payload["instrument_id"]),
            quantity=int(payload["quantity"]),
            execution_price=price,
            execution_price_currency=str(
                payload.get("execution_price_currency") or "USD"
            ),
            sequence_number=int(payload.get("sequence_number") or 0),
            executed_at=executed_at,
        )

    @staticmethod
    def _to_order_command(
        event_type: str, payload: dict[str, Any]
    ) -> RecordOrderEventCommand:
        price = None
        raw_price = payload.get("limit_price", payload.get("price"))
        if raw_price is not None and raw_price != "":
            price = Decimal(str(raw_price))

        occurred = payload.get("occurred_at")
        occurred_at = None
        if occurred:
            occurred_at = datetime.fromisoformat(str(occurred).replace("Z", "+00:00"))

        return RecordOrderEventCommand(
            order_id=str(payload["order_id"]),
            trader_id=str(payload.get("trader_id") or ""),
            instrument_id=str(payload.get("instrument_id") or ""),
            event_type=event_type,
            side=payload.get("side"),
            order_type=payload.get("order_type"),
            quantity=payload.get("quantity"),
            filled_quantity=payload.get("filled_quantity")
            or payload.get("fill_quantity"),
            remaining_quantity=payload.get("remaining_quantity"),
            price=price,
            price_currency=payload.get("limit_price_currency")
            or payload.get("price_currency"),
            status=payload.get("status"),
            occurred_at=occurred_at,
        )
