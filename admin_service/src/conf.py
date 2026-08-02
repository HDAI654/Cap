import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_file = BASE_DIR / ".env"

if os.getenv("APP_NAME", None) is None:
    load_dotenv(env_file)


class Config:
    APP_NAME: str = os.getenv("APP_NAME", "AdminService")
    APP_ENV: str = os.getenv("APP_ENV", "development")

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///:memory:",
    )

    # Auth: public key used only to verify JWTs issued by the Auth service.
    # PEM text; newlines may be escaped as \n in env files.
    AUTH_PUBLIC_KEY: str = os.getenv("AUTH_PUBLIC_KEY", "").replace("\\n", "\n")
    AUTH_JWT_ALGORITHM: str = os.getenv("AUTH_JWT_ALGORITHM", "RS256")
    AUTH_ADMIN_ROLE: str = os.getenv("AUTH_ADMIN_ROLE", "ADMIN")
