"""Balance & History Service — event consumer only (no HTTP API).

Architecture: Event Consumers → BHS → Persistent Store
(Wallet Service reads history/balances from the same store.)

Run:
    PYTHONPATH=.:balance_history_service python -m src.worker
"""

from __future__ import annotations

import asyncio
import logging
import signal

from src.conf import Config
from src.database import async_session_maker, engine
from src.infrastructure.persistence.models import Base
from src.infrastructure.persistence.unit_of_work import SQLAlchemyUnitOfWork
from src.logging_config import setup_logging

logger = logging.getLogger(__name__)


async def run() -> None:
    setup_logging()
    logger.info("Starting Balance & History worker env=%s", Config.APP_ENV)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    def uow_factory() -> SQLAlchemyUnitOfWork:
        return SQLAlchemyUnitOfWork(async_session_maker)

    from src.application.record_order_event import RecordOrderEventHandler
    from src.application.record_trade import RecordTradeHandler

    class _TradeHandler:
        async def handle(self, command):
            await RecordTradeHandler(uow_factory()).handle(command)

    class _OrderHandler:
        async def handle(self, command):
            await RecordOrderEventHandler(uow_factory()).handle(command)

    if not Config.RABBITMQ_ENABLED:
        logger.error(
            "RABBITMQ_ENABLED=false — BHS is an event consumer and cannot run without the bus."
        )
        return

    from src.infrastructure.messaging.history_event_consumer import (
        HistoryEventConsumer,
    )

    consumer = HistoryEventConsumer(
        url=Config.RABBITMQ_URL,
        trade_exchange=Config.RABBITMQ_TRADE_EVENTS_EXCHANGE,
        order_exchange=Config.RABBITMQ_ORDER_EVENTS_EXCHANGE,
        queue_name=Config.RABBITMQ_HISTORY_QUEUE,
        record_trade_handler=_TradeHandler(),  # type: ignore[arg-type]
        record_order_handler=_OrderHandler(),  # type: ignore[arg-type]
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
    await engine.dispose()
    logger.info("Balance & History worker stopped")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
