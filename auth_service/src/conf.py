"""Auth service configuration."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_SERVICE_DIR = Path(__file__).resolve().parent.parent
_env = _SERVICE_DIR / ".env"
if os.getenv("APP_NAME") is None and _env.exists():
    load_dotenv(_env)

_PRIVATE_KEY_PATH = Path(
    os.getenv("AUTH_PRIVATE_KEY_PATH", str(_SERVICE_DIR / "keys" / "private.pem"))
)
_PUBLIC_KEY_PATH = Path(
    os.getenv("AUTH_PUBLIC_KEY_PATH", str(_SERVICE_DIR / "keys" / "public.pem"))
)


class Config:
    """Environment-backed settings for Auth Service."""

    APP_NAME: str = os.getenv("APP_NAME", "CapAuth")
    APP_ENV: str = os.getenv("APP_ENV", "development")

    VERIFY_EMAIL_EXPIRE_MINUTES: int = int(
        os.getenv("VERIFY_EMAIL_EXPIRE_MINUTES", "1440")
    )
    RESET_PASSWORD_EXPIRE_MINUTES: int = int(
        os.getenv("RESET_PASSWORD_EXPIRE_MINUTES", "60")
    )
    VERIFY_EMAIL_URL: str = os.getenv(
        "VERIFY_EMAIL_URL", "http://localhost:3000/verify-email"
    )
    RESET_PASSWORD_URL: str = os.getenv(
        "RESET_PASSWORD_URL", "http://localhost:3000/reset-password"
    )
    SUPPORT_EMAIL: str = os.getenv("SUPPORT_EMAIL", "support@example.com")

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_ENABLED: bool = os.getenv("REDIS_ENABLED", "false").lower() in (
        "1",
        "true",
        "yes",
    )
    SESSION_KEY_PREFIX: str = os.getenv("SESSION_KEY_PREFIX", "auth:session:")
    USER_SESSIONS_KEY_PREFIX: str = os.getenv(
        "USER_SESSIONS_KEY_PREFIX", "auth:user_sessions:"
    )
    VERIFICATION_TOKEN_KEY_PREFIX: str = os.getenv(
        "VERIFICATION_TOKEN_KEY_PREFIX", "auth:verify:"
    )

    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    RABBITMQ_ENABLED: bool = os.getenv("RABBITMQ_ENABLED", "false").lower() in (
        "1",
        "true",
        "yes",
    )
    RABBITMQ_EXCHANGE: str = os.getenv("RABBITMQ_EXCHANGE", "auth.events")

    AUTH_TOKEN_ALGORITHM: str = os.getenv("AUTH_TOKEN_ALGORITHM", "RS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
    )
    REFRESH_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", "43200")
    )
    ROTATE_THRESHOLD_MINUTES: int = int(os.getenv("ROTATE_THRESHOLD_MINUTES", "4320"))

    ADMIN_PASSWORD_HASH: str = os.getenv("ADMIN_PASSWORD_HASH", "")

    # Comma-separated blocked addresses / domains for signup
    BLOCKED_EMAILS: set[str] = {
        e.strip().lower()
        for e in os.getenv("BLOCKED_EMAILS", "").split(",")
        if e.strip()
    }
    BLOCKED_EMAIL_DOMAINS: set[str] = {
        d.strip().lower()
        for d in os.getenv("BLOCKED_EMAIL_DOMAINS", "").split(",")
        if d.strip()
    }
    BLOCKED_EMAILS_REDIS_KEY: str = os.getenv(
        "BLOCKED_EMAILS_REDIS_KEY", "auth:blocked_emails"
    )

    AUTH_TOKEN_PRIVATE_KEY: str = (
        _PRIVATE_KEY_PATH.read_text() if _PRIVATE_KEY_PATH.exists() else ""
    )
    AUTH_TOKEN_PUBLIC_KEY: str = (
        _PUBLIC_KEY_PATH.read_text() if _PUBLIC_KEY_PATH.exists() else ""
    )
