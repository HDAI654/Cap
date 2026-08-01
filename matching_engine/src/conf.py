import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_file = BASE_DIR / ".env"

if os.getenv("APP_NAME", None) is None:
    load_dotenv(env_file)


class Config:
    APP_NAME: str = os.getenv("APP_NAME", "MatchingEngine")
    APP_ENV: str = os.getenv("APP_ENV", "development")

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
    RABBITMQ_TRADE_EVENTS_EXCHANGE: str = os.getenv(
        "RABBITMQ_TRADE_EVENTS_EXCHANGE",
        "trade.events",
    )
    RABBITMQ_EXCHANGE_TYPE: str = os.getenv("RABBITMQ_EXCHANGE_TYPE", "topic")
    RABBITMQ_MATCHING_QUEUE: str = os.getenv(
        "RABBITMQ_MATCHING_QUEUE",
        "matching_engine.orders",
    )

    REDIS_ENABLED: bool = os.getenv("REDIS_ENABLED", "false").lower() in (
        "1",
        "true",
        "yes",
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
