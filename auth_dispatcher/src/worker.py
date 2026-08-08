import asyncio
import logging
import signal
from src.application.dispatch_auth_email import DispatchAuthEmailHandler
from src.conf import Config
from src.infrastructure.messaging.event_consumer import AuthEventConsumer
from src.infrastructure.messaging.noop_email_sender import NoOpEmailSender
from src.infrastructure.messaging.smtp_email_sender import SmtpEmailSender
from src.logging_config import setup_logging

logger = logging.getLogger(__name__)


def _build_email_sender():
    if Config.SMTP_ENABLED:
        return SmtpEmailSender()
    return NoOpEmailSender()


async def run() -> None:
    setup_logging()
    logger.info("Starting Auth Dispatcher env=%s", Config.APP_ENV)

    if not Config.RABBITMQ_ENABLED:
        logger.error(
            "RABBITMQ_ENABLED=false — Auth Dispatcher cannot run without the bus."
        )
        return

    handler = DispatchAuthEmailHandler(_build_email_sender())
    consumer = AuthEventConsumer(
        url=Config.RABBITMQ_URL,
        exchange_name=Config.RABBITMQ_AUTH_EVENTS_EXCHANGE,
        queue_name=Config.RABBITMQ_QUEUE,
        handler=handler,
        exchange_type=Config.RABBITMQ_EXCHANGE_TYPE,
        prefetch_count=Config.RABBITMQ_PREFETCH,
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
    logger.info("Auth Dispatcher stopped")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
