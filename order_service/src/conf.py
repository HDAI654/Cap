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
