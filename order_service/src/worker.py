"""Order Service fill worker — applies ME OrderFilled events to OIS aggregates.

Run:
    PYTHONPATH=.:order_service python -m src.worker
"""

from __future__ import annotations

import asyncio
import logging
import signal

from src.application.fill_order import FillOrderHandler
from src.conf import Config
from src.database import async_session_maker, engine
from src.infrastructure.messaging.fill_event_consumer import FillEventConsumer
from src.infrastructure.messaging.noop_event_publisher import NoOpEventPublisher
from src.infrastructure.persistence.models import Base
from src.infrastructure.persistence.unit_of_work import SQLAlchemyUnitOfWork
from src.logging_config import setup_logging

logger = logging.getLogger(__name__)


async def run() -> None:
    setup_logging()
    logger.info("Starting OIS fill worker env=%s", Config.APP_ENV)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    def fill_handler() -> FillOrderHandler:
        return FillOrderHandler(
            SQLAlchemyUnitOfWork(async_session_maker),
            NoOpEventPublisher(),
        )

    class _Handler:
        async def handle(self, command):
            await fill_handler().handle(command)

    if not Config.RABBITMQ_ENABLED:
        logger.error("RABBITMQ_ENABLED=false — fill worker cannot run without the bus.")
        return

    consumer = FillEventConsumer(
        url=Config.RABBITMQ_URL,
        exchange_name=Config.RABBITMQ_TRADE_EVENTS_EXCHANGE,
        queue_name=Config.RABBITMQ_FILL_QUEUE,
        fill_handler=_Handler(),  # type: ignore[arg-type]
        exchange_type=Config.RABBITMQ_EXCHANGE_TYPE,
    )
    await consumer.start()

    stop_event = asyncio.Event()

    def _signal_handler() -> None:
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _signal_handler)
        except NotImplementedError:
            pass

    await stop_event.wait()
    await consumer.stop()
    await engine.dispose()
    logger.info("OIS fill worker stopped")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
