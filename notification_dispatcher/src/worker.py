"""Notification Dispatcher — event consumer only.

Architecture: Event Consumers → ND → push real-time updates → Notification Service

Run:
    PYTHONPATH=.:notification_dispatcher python -m src.worker
"""

from __future__ import annotations

import asyncio
import logging
import signal

from src.application.dispatch_event import DispatchEventHandler
from src.conf import Config
from src.infrastructure.messaging.event_consumer import DispatcherEventConsumer
from src.infrastructure.messaging.http_notification_gateway import (
    HttpNotificationGateway,
)
from src.infrastructure.messaging.noop_notification_gateway import (
    NoOpNotificationGateway,
)
from src.logging_config import setup_logging

logger = logging.getLogger(__name__)


async def run() -> None:
    setup_logging()
    logger.info("Starting Notification Dispatcher env=%s", Config.APP_ENV)

    if Config.APP_ENV == "development" and not Config.RABBITMQ_ENABLED:
        gateway = NoOpNotificationGateway()
    else:
        gateway = HttpNotificationGateway(
            base_url=Config.NOTIFICATION_SERVICE_URL,
            push_path=Config.NOTIFICATION_PUSH_PATH,
        )

    handler = DispatchEventHandler(gateway)

    if not Config.RABBITMQ_ENABLED:
        logger.error(
            "RABBITMQ_ENABLED=false — Notification Dispatcher cannot run without the bus."
        )
        return

    consumer = DispatcherEventConsumer(
        url=Config.RABBITMQ_URL,
        trade_exchange=Config.RABBITMQ_TRADE_EVENTS_EXCHANGE,
        order_exchange=Config.RABBITMQ_ORDER_EVENTS_EXCHANGE,
        queue_name=Config.RABBITMQ_DISPATCHER_QUEUE,
        dispatch_handler=handler,
        exchange_type=Config.RABBITMQ_EXCHANGE_TYPE,
    )
    await consumer.start()

    stop_event = asyncio.Event()

    def _signal_handler() -> None:
        logger.info("Shutdown signal received")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _signal_handler)
        except NotImplementedError:
            pass

    await stop_event.wait()
    await consumer.stop()
    logger.info("Notification Dispatcher stopped")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
