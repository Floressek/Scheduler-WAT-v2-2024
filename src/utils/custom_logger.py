import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
import pytz
import os
os.environ['FORCE_COLOR'] = '1'

# Define timezone for Poland
POLAND_TZ = pytz.timezone('Europe/Warsaw')

# ANSI color codes
COLORS = {
    'TIMESTAMP': '\033[36m',  # Cyan
    'DEBUG': '\033[94m',      # Light Blue
    'INFO': '\033[92m',       # Light Green
    'WARNING': '\033[93m',    # Light Yellow
    'ERROR': '\033[91m',      # Light Red
    'CRITICAL': '\033[95m',   # Light Magenta
    'RESET': '\033[0m'        # Reset to default color
}

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        levelname = record.levelname
        timestamp = self.formatTime(record, self.datefmt)
        message = super().format(record)
        return (f"{COLORS['TIMESTAMP']}{timestamp}{COLORS['RESET']} "
                f"[{COLORS.get(levelname, COLORS['RESET'])}{levelname}{COLORS['RESET']}] "
                f"{record.module}:{record.funcName}:{record.lineno} - {message}")

    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, POLAND_TZ)
        return dt.strftime(datefmt or '%Y-%m-%d %H:%M:%S %Z')

def setup_custom_logger(name, log_file, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # File formatter (unchanged)
    file_formatter = logging.Formatter('{asctime} {levelname} {module}:{funcName}:{lineno} - {message}',
                                       datefmt='%Y-%m-%d %H:%M:%S %Z', style='{')

    # File handler (unchanged)
    file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(level)

    # Console handler with refined color
    console_formatter = ColoredFormatter(datefmt='%Y-%m-%d %H:%M:%S')
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