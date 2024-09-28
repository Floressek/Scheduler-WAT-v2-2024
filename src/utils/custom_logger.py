import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
import pytz
from rich.logging import RichHandler
from rich.console import Console
from rich.theme import Theme

# Definicja strefy czasowej dla Polski
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
        if datefmt:
            s = dt.strftime(datefmt)
        else:
            s = dt.isoformat(timespec='milliseconds')
        return s


def setup_custom_logger(name, log_file, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Formatter dla pliku
    file_formatter = PolandFormatter('{asctime} {levelname} {module}:{funcName}:{lineno} - {message}',
                                     datefmt='%Y-%m-%d %H:%M:%S %Z', style='{')

    # Handler dla pliku
    file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(level)

    # Rich handler dla konsoli
    console_handler = RichHandler(console=console, rich_tracebacks=True)
    console_handler.setLevel(level)

    # Dodanie handlerów do loggera
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Upewnij się, że katalog logów istnieje
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Stwórz loggery
main_logger = setup_custom_logger('[Main]', os.path.join(log_dir, 'main.log'))
scheduler_logger = setup_custom_logger('[Scheduler]', os.path.join(log_dir, 'scheduler.log'))
google_api_logger = setup_custom_logger('[GoogleAPI]', os.path.join(log_dir, 'google_api.log'))
