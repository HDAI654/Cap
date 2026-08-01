import logging
import logging.config
from src.conf import Config
from logging.handlers import RotatingFileHandler
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "app.log"
APP_ENV = Config.APP_ENV


def setup_logging():
    LOG_DIR.mkdir(exist_ok=True)

    if APP_ENV == "development":
        root_level = "DEBUG"
        console_level = "DEBUG"
        file_level = "INFO"
    else:
        root_level = "INFO"
        console_level = "ERROR"
        file_level = "INFO"

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": console_level,
                "formatter": "standard",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": file_level,
                "formatter": "standard",
                "filename": str(LOG_FILE),
                "maxBytes": 20 * 1024 * 1024,
                "backupCount": 3,
                "encoding": "utf-8",
            },
        },
        "root": {
            "level": root_level,
            "handlers": ["console", "file"] if root_level != "DEBUG" else ["console"],
        },
    }

    logging.config.dictConfig(logging_config)
