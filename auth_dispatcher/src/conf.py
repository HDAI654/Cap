import os
from pathlib import Path
from dotenv import load_dotenv

_BASE = Path(__file__).resolve().parent.parent
_env = _BASE / ".env"
if os.getenv("APP_NAME") is None and _env.exists():
    load_dotenv(_env)


class Config:
    APP_NAME: str = os.getenv("APP_NAME", "AuthDispatcher")
    APP_ENV: str = os.getenv("APP_ENV", "development")

    RABBITMQ_ENABLED: bool = os.getenv("RABBITMQ_ENABLED", "false").lower() in (
        "1",
        "true",
        "yes",
    )
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    RABBITMQ_AUTH_EVENTS_EXCHANGE: str = os.getenv(
        "RABBITMQ_AUTH_EVENTS_EXCHANGE", "auth.events"
    )
    RABBITMQ_EXCHANGE_TYPE: str = os.getenv("RABBITMQ_EXCHANGE_TYPE", "topic")
    RABBITMQ_QUEUE: str = os.getenv(
        "RABBITMQ_AUTH_DISPATCHER_QUEUE", "auth_dispatcher.events"
    )
    RABBITMQ_PREFETCH: int = int(os.getenv("RABBITMQ_PREFETCH", "10"))

    # SMTP (optional — NoOp when SMTP_ENABLED=false)
    SMTP_ENABLED: bool = os.getenv("SMTP_ENABLED", "false").lower() in (
        "1",
        "true",
        "yes",
    )
    SMTP_HOST: str = os.getenv("SMTP_HOST", "localhost")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "noreply@cap.local")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() in (
        "1",
        "true",
        "yes",
    )

    APP_DISPLAY_NAME: str = os.getenv("APP_DISPLAY_NAME", "Cap")
    VERIFY_EMAIL_URL: str = os.getenv(
        "VERIFY_EMAIL_URL", "http://localhost:3000/verify-email"
    )
    RESET_PASSWORD_URL: str = os.getenv(
        "RESET_PASSWORD_URL", "http://localhost:3000/reset-password"
    )
    SUPPORT_EMAIL: str = os.getenv("SUPPORT_EMAIL", "support@cap.local")
