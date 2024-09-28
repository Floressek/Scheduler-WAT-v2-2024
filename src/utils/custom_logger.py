import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
import pytz
from rich.logging import RichHandler
from rich.console import Console
from rich.theme import Theme

# Define timezone for Poland
POLAND_TZ = pytz.timezone('Europe/Warsaw')

custom_theme = Theme({
    "info": "green",
    "warning": "yellow",
    "error": "red",
    "critical": "bold red",
    "debug": "blue",
})

console = Console(theme=custom_theme)


class PolandFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, POLAND_TZ)
        return dt.strftime('%Y-%m-%d %H:%M:%S %Z')


def setup_custom_logger(name, log_file, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # File formatter
    file_formatter = PolandFormatter(
        '%(asctime)s | %(levelname)-8s | %(name)-12s | %(message)s'
    )

    # File handler
    file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(level)

    # Rich console handler
    console_handler = RichHandler(
        console=console,
        rich_tracebacks=True,
        show_time=True,
        show_path=True,
        markup=True
    )
    console_handler.setLevel(level)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Ensure log directory exists
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Create loggers
main_logger = setup_custom_logger('Main', os.path.join(log_dir, 'main.log'))
scheduler_logger = setup_custom_logger('Scheduler', os.path.join(log_dir, 'scheduler.log'))
google_api_logger = setup_custom_logger('GoogleAPI', os.path.join(log_dir, 'google_api.log'))
