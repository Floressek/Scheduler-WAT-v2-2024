import logging
import os
from datetime import datetime
from logging import Logger
from logging.handlers import RotatingFileHandler

import pytz

from src.config import TIMEZONE

os.environ["FORCE_COLOR"] = "1"

POLAND_TZ = pytz.timezone(TIMEZONE)

COLORS: dict[str, str] = {
    "TIMESTAMP": "\033[36m",
    "DEBUG": "\033[94m",
    "INFO": "\033[92m",
    "WARNING": "\033[93m",
    "ERROR": "\033[91m",
    "CRITICAL": "\033[95m",
    "RESET": "\033[0m",
}


class ColoredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        levelname = record.levelname
        timestamp = self.formatTime(record, self.datefmt)
        message = super().format(record)
        return (
            f"{COLORS['TIMESTAMP']}{timestamp}{COLORS['RESET']} "
            f"[{COLORS.get(levelname, COLORS['RESET'])}{levelname}{COLORS['RESET']}] "
            f"{record.module}:{record.funcName}:{record.lineno} - {message}"
        )

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        dt = datetime.fromtimestamp(record.created, POLAND_TZ)
        return dt.strftime(datefmt or "%Y-%m-%d %H:%M:%S %Z")


def setup_custom_logger(name: str, log_file: str, level: int = logging.INFO) -> Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    file_formatter = logging.Formatter(
        "{asctime} {levelname} {module}:{funcName}:{lineno} - {message}",
        datefmt="%Y-%m-%d %H:%M:%S %Z",
        style="{",
    )
    file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(level)

    console_formatter = ColoredFormatter(datefmt="%Y-%m-%d %H:%M:%S")
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(level)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

main_logger: Logger = setup_custom_logger("[Main]", os.path.join(log_dir, "main.log"))
scheduler_logger: Logger = setup_custom_logger("[Scheduler]", os.path.join(log_dir, "scheduler.log"))
google_api_logger: Logger = setup_custom_logger("[GoogleAPI]", os.path.join(log_dir, "google_api.log"))
