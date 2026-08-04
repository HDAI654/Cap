import json
import logging
from decimal import Decimal, InvalidOperation
from typing import Any

from src.application.settle_trade import SettleTradeCommand, SettleTradeHandler
from src.exceptions import DatabaseConnectionError

logger = logging.getLogger(__name__)


class TradeSettlementConsumer:
    """Consumes TradeExecuted and settles buyer/seller wallets."""

    def __init__(
        self,
        url: str,
        exchange_name: str,
        queue_name: str,
        settle_handler: SettleTradeHandler,
        exchange_type: str = "topic",
        prefetch_count: int = 16,
    ) -> None:
        self._url = url
        self._exchange_name = exchange_name
        self._queue_name = queue_name
        self._exchange_type = exchange_type
        self._prefetch_count = prefetch_count
        self._settle_handler = settle_handler
        self._connection = None
        self._channel = None

    async def start(self) -> None:
        try:
            import aio_pika
            from aio_pika import ExchangeType
        except ImportError as exc:
            raise DatabaseConnectionError(
                "aio-pika is required for settlement consumer"
            ) from exc

        self._connection = await aio_pika.connect_robust(self._url)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=self._prefetch_count)

        exchange = await self._channel.declare_exchange(
            self._exchange_name,
            ExchangeType(self._exchange_type),
            durable=True,
        )
        queue = await self._channel.declare_queue(self._queue_name, durable=True)
        await queue.bind(exchange, routing_key="TradeExecuted")
        await queue.consume(self._on_message)
        logger.info("TradeSettlementConsumer started: queue=%s", self._queue_name)

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
                logger.error("Invalid settlement message: %s", exc)
                return

            try:
                price = Decimal(str(payload["execution_price"]))
            except (KeyError, InvalidOperation, TypeError) as exc:
                logger.error("TradeExecuted missing/invalid price: %s", exc)
                return

            command = SettleTradeCommand(
                trade_id=str(payload.get("trade_id", "")),
                buyer_id=str(payload["buyer_id"]),
                seller_id=str(payload["seller_id"]),
                instrument_id=str(payload["instrument_id"]),
                quantity=int(payload["quantity"]),
                execution_price=price,
                execution_price_currency=str(
                    payload.get("execution_price_currency") or "USD"
                ),
            )
            try:
                await self._settle_handler.handle(command)
            except Exception:
                logger.exception("Settlement failed trade_id=%s", command.trade_id)
                raise
