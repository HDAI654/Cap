import json
import logging
from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
from typing import Any

from src.domain.events.matching_events import DomainEvent
from src.domain.ports.event_publisher import EventPublisher
from src.exceptions import MessagingConnectionError, MessagingPublishError

logger = logging.getLogger(__name__)


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


class RabbitMQEventPublisher(EventPublisher):
    """Publishes matching events to a RabbitMQ topic exchange (trade.events)."""

    def __init__(
        self,
        url: str,
        exchange_name: str,
        exchange_type: str = "topic",
    ) -> None:
        self._url = url
        self._exchange_name = exchange_name
        self._exchange_type = exchange_type
        self._connection = None
        self._channel = None
        self._exchange = None

    async def connect(self) -> None:
        try:
            import aio_pika
        except ImportError as exc:
            raise MessagingConnectionError(
                "aio-pika is required for RabbitMQEventPublisher. "
                "Install it with: pip install aio-pika"
            ) from exc

        try:
            self._connection = await aio_pika.connect_robust(self._url)
            self._channel = await self._connection.channel()
            self._exchange = await self._channel.declare_exchange(
                self._exchange_name,
                aio_pika.ExchangeType(self._exchange_type),
                durable=True,
            )
            logger.info(
                "Publisher connected: exchange=%s",
                self._exchange_name,
            )
        except Exception as exc:
            logger.exception("Failed to connect publisher to RabbitMQ")
            raise MessagingConnectionError(
                f"Failed to connect to RabbitMQ: {exc}"
            ) from exc

    async def close(self) -> None:
        if self._connection is not None and not self._connection.is_closed:
            await self._connection.close()
            logger.info("Publisher RabbitMQ connection closed")
        self._connection = None
        self._channel = None
        self._exchange = None

    async def publish(self, event: DomainEvent) -> None:
        if self._exchange is None:
            await self.connect()

        try:
            import aio_pika
        except ImportError as exc:
            raise MessagingConnectionError(
                "aio-pika is required for RabbitMQEventPublisher."
            ) from exc

        body = json.dumps(asdict(event), default=_json_default).encode("utf-8")
        message = aio_pika.Message(
            body=body,
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            type=event.event_type,
        )

        try:
            await self._exchange.publish(message, routing_key=event.event_type)
            logger.info("Published event_type=%s", event.event_type)
        except Exception as exc:
            logger.exception("Failed to publish event_type=%s", event.event_type)
            raise MessagingPublishError(
                f"Failed to publish event '{event.event_type}': {exc}"
            ) from exc
