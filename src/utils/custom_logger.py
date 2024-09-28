import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import pytz
import os
os.environ['FORCE_COLOR'] = '1'


# Define timezone for Poland
POLAND_TZ = pytz.timezone('Europe/Warsaw')

# ANSI color codes
COLORS = {
    'DEBUG': '\033[94m',    # Blue
    'INFO': '\033[92m',     # Green
    'WARNING': '\033[93m',  # Yellow
    'ERROR': '\033[91m',    # Red
    'CRITICAL': '\033[95m', # Magenta
    'RESET': '\033[0m'      # Reset to default color
}

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        levelname = record.levelname
        message = super().format(record)
        return f"{COLORS.get(levelname, COLORS['RESET'])}{message}{COLORS['RESET']}"

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

    # File formatter (unchanged)
    file_formatter = PolandFormatter('{asctime} {levelname} {module}:{funcName}:{lineno} - {message}',
                                     datefmt='%Y-%m-%d %H:%M:%S %Z', style='{')

    # File handler (unchanged)
    file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(level)

    # Console handler with color
    console_formatter = ColoredFormatter('{asctime} [{levelname}] {module}:{funcName}:{lineno} - {message}',
                                         datefmt='%Y-%m-%d %H:%M:%S', style='{')
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(level)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# Ensure log directory exists
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Create loggers
main_logger = setup_custom_logger('[Main]', os.path.join(log_dir, 'main.log'))
scheduler_logger = setup_custom_logger('[Scheduler]', os.path.join(log_dir, 'scheduler.log'))
google_api_logger = setup_custom_logger('[GoogleAPI]', os.path.join(log_dir, 'google_api.log'))