"""Wallet settlement worker — settles TradeExecuted against wallets.

Run:
    PYTHONPATH=.:wallet_service python -m src.worker
"""

from __future__ import annotations

import asyncio
import logging
import signal

from src.application.settle_trade import SettleTradeHandler
from src.conf import Config
from src.database import async_session_maker, engine
from src.infrastructure.messaging.trade_settlement_consumer import (
    TradeSettlementConsumer,
)
from src.infrastructure.persistence.models import Base
from src.infrastructure.persistence.unit_of_work import SQLAlchemyUnitOfWork

logger = logging.getLogger(__name__)


async def run() -> None:
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting wallet settlement worker env=%s", Config.APP_ENV)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    class _Handler:
        async def handle(self, command):
            await SettleTradeHandler(SQLAlchemyUnitOfWork(async_session_maker)).handle(
                command
            )

    if not Config.RABBITMQ_ENABLED:
        logger.error("RABBITMQ_ENABLED=false — settlement worker idle.")
        return

    consumer = TradeSettlementConsumer(
        url=Config.RABBITMQ_URL,
        exchange_name=Config.RABBITMQ_TRADE_EVENTS_EXCHANGE,
        queue_name=Config.RABBITMQ_SETTLEMENT_QUEUE,
        settle_handler=_Handler(),  # type: ignore[arg-type]
        exchange_type=Config.RABBITMQ_EXCHANGE_TYPE,
    )
    await consumer.start()

    stop_event = asyncio.Event()

    def _stop() -> None:
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _stop)
        except NotImplementedError:
            pass

    await stop_event.wait()
    await consumer.stop()
    await engine.dispose()
    logger.info("Wallet settlement worker stopped")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
