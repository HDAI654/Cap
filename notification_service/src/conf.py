import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_file = BASE_DIR / ".env"

if os.getenv("APP_NAME", None) is None:
    load_dotenv(env_file)


class Config:
    APP_NAME: str = os.getenv("APP_NAME", "NotificationService")
    APP_ENV: str = os.getenv("APP_ENV", "development")
