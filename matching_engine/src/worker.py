import asyncio
import logging
import signal
from src.conf import Config
from src.infrastructure.book.in_memory_order_book_registry import (
    InMemoryOrderBookRegistry,
)
from src.infrastructure.cache.noop_market_data_cache import NoOpMarketDataCache
from src.infrastructure.messaging.noop_event_publisher import NoOpEventPublisher
from src.logging_config import setup_logging

logger = logging.getLogger(__name__)


def _build_publisher():
    if Config.RABBITMQ_ENABLED:
        from src.infrastructure.messaging.rabbitmq_event_publisher import (
            RabbitMQEventPublisher,
        )

        return RabbitMQEventPublisher(
            url=Config.RABBITMQ_URL,
            exchange_name=Config.RABBITMQ_TRADE_EVENTS_EXCHANGE,
            exchange_type=Config.RABBITMQ_EXCHANGE_TYPE,
        )
    return NoOpEventPublisher()


def _build_cache():
    if Config.REDIS_ENABLED:
        from src.infrastructure.cache.redis_market_data_cache import (
            RedisMarketDataCache,
        )

        return RedisMarketDataCache(url=Config.REDIS_URL)
    return NoOpMarketDataCache()


async def run() -> None:
    setup_logging()
    logger.info("Starting Matching Engine worker env=%s", Config.APP_ENV)

    registry = InMemoryOrderBookRegistry()
    publisher = _build_publisher()
    cache = _build_cache()

    if hasattr(publisher, "connect"):
        await publisher.connect()
    if hasattr(cache, "connect"):
        await cache.connect()

    from src.application.cancel_resting_order import CancelRestingOrderHandler
    from src.application.process_incoming_order import ProcessIncomingOrderHandler

    process_handler = ProcessIncomingOrderHandler(registry, publisher, cache)
    cancel_handler = CancelRestingOrderHandler(registry, publisher, cache)

    consumer = None
    if Config.RABBITMQ_ENABLED:
        from src.infrastructure.messaging.order_event_consumer import (
            OrderEventConsumer,
        )

        consumer = OrderEventConsumer(
            url=Config.RABBITMQ_URL,
            exchange_name=Config.RABBITMQ_ORDER_EVENTS_EXCHANGE,
            queue_name=Config.RABBITMQ_MATCHING_QUEUE,
            process_handler=process_handler,
            cancel_handler=cancel_handler,
            exchange_type=Config.RABBITMQ_EXCHANGE_TYPE,
        )
        await consumer.start()
    else:
        logger.warning(
            "RABBITMQ_ENABLED=false — worker idle (no consumer). "
            "Enable RabbitMQ for production matching."
        )

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

    if consumer is not None:
        await consumer.stop()
    if hasattr(publisher, "close"):
        await publisher.close()
    if hasattr(cache, "close"):
        await cache.close()

    logger.info("Matching Engine worker stopped")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
