import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_file = BASE_DIR / ".env"

if os.getenv("APP_NAME", None) is None:
    load_dotenv(env_file)


class Config:
    # App
    APP_NAME: str = os.getenv("APP_NAME", "OrderService")
    APP_ENV: str = os.getenv("APP_ENV", "development")

    # DB
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///:memory:",
    )

    # Event bus (RabbitMQ)
    # Disabled by default so unit/e2e tests and local runs need no broker.
    RABBITMQ_ENABLED: bool = os.getenv("RABBITMQ_ENABLED", "false").lower() in (
        "1",
        "true",
        "yes",
    )
    RABBITMQ_URL: str = os.getenv(
        "RABBITMQ_URL",
        "amqp://guest:guest@localhost:5672/",
    )
    RABBITMQ_ORDER_EVENTS_EXCHANGE: str = os.getenv(
        "RABBITMQ_ORDER_EVENTS_EXCHANGE",
        "order.events",
    )
    RABBITMQ_EXCHANGE_TYPE: str = os.getenv(
        "RABBITMQ_EXCHANGE_TYPE",
        "topic",
    )

    # Cross-service integrations (disabled by default for isolated tests)
    WALLET_INTEGRATION_ENABLED: bool = os.getenv(
        "WALLET_INTEGRATION_ENABLED", "false"
    ).lower() in ("1", "true", "yes")
    WALLET_SERVICE_URL: str = os.getenv(
        "WALLET_SERVICE_URL",
        "http://localhost:8001",
    )
    ADMIN_INTEGRATION_ENABLED: bool = os.getenv(
        "ADMIN_INTEGRATION_ENABLED", "false"
    ).lower() in ("1", "true", "yes")
    ADMIN_SERVICE_URL: str = os.getenv(
        "ADMIN_SERVICE_URL",
        "http://localhost:8002",
    )
    RABBITMQ_TRADE_EVENTS_EXCHANGE: str = os.getenv(
        "RABBITMQ_TRADE_EVENTS_EXCHANGE",
        "trade.events",
    )
    RABBITMQ_FILL_QUEUE: str = os.getenv(
        "RABBITMQ_FILL_QUEUE",
        "order_service.fills",
    )
