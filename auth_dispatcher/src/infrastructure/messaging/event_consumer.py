import json
import logging
from typing import Any

from src.application.dispatch_auth_email import (
    EVENT_VERIFICATION_TOKEN_CREATED,
    DispatchAuthEmailHandler,
)
from src.exceptions import MessagingConnectionError, MessagingError

logger = logging.getLogger(__name__)

_AUTH_EVENTS = (EVENT_VERIFICATION_TOKEN_CREATED,)


class AuthEventConsumer:
    """Bind queue to auth exchange and dispatch messages."""

    def __init__(
        self,
        *,
        url: str,
        exchange_name: str,
        queue_name: str,
        handler: DispatchAuthEmailHandler,
        exchange_type: str = "topic",
        prefetch_count: int = 10,
    ) -> None:
        self._url = url
        self._exchange_name = exchange_name
        self._queue_name = queue_name
        self._handler = handler
        self._exchange_type = exchange_type
        self._prefetch_count = prefetch_count
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
            for key in _AUTH_EVENTS:
                await queue.bind(exchange, routing_key=key)

            await queue.consume(self._on_message)
            logger.info(
                "AuthEventConsumer started exchange=%s queue=%s",
                self._exchange_name,
                self._queue_name,
            )
        except Exception as exc:
            raise MessagingConnectionError(str(exc)) from exc

    async def stop(self) -> None:
        if self._connection is not None and not self._connection.is_closed:
            await self._connection.close()
        self._connection = None
        self._channel = None

    async def _on_message(self, message) -> None:
        async with message.process(requeue=False):
            try:
                payload = json.loads(message.body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                logger.exception("Invalid message body — drop")
                return

            event_type = payload.get("event_type") or message.routing_key or ""
            try:
                await self._handler.handle(str(event_type), payload)
            except Exception:
                logger.exception(
                    "Handler failed event_type=%s — message acked (no requeue)",
                    event_type,
                )
