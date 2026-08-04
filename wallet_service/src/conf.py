import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_file = BASE_DIR / ".env"

if os.getenv("APP_NAME", None) is None:
    load_dotenv(env_file)


class Config:
    # App
    APP_NAME: str = os.getenv("APP_NAME", "MyApp")
    APP_ENV: str = os.getenv("APP_ENV", "development")

    # DB
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///:memory:",
    )

    # Settlement consumer (TradeExecuted)
    RABBITMQ_ENABLED: bool = os.getenv("RABBITMQ_ENABLED", "false").lower() in (
        "1",
        "true",
        "yes",
    )
    RABBITMQ_URL: str = os.getenv(
        "RABBITMQ_URL",
        "amqp://guest:guest@localhost:5672/",
    )
    RABBITMQ_TRADE_EVENTS_EXCHANGE: str = os.getenv(
        "RABBITMQ_TRADE_EVENTS_EXCHANGE",
        "trade.events",
    )
    RABBITMQ_EXCHANGE_TYPE: str = os.getenv("RABBITMQ_EXCHANGE_TYPE", "topic")
    RABBITMQ_SETTLEMENT_QUEUE: str = os.getenv(
        "RABBITMQ_SETTLEMENT_QUEUE",
        "wallet_service.settlement",
    )
