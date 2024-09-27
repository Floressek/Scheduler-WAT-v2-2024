import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
import pytz
import colorama
from colorama import Fore, Style

# Inicjalizacja Colorama
colorama.init(autoreset=True)

# Definicja strefy czasowej dla Polski
POLAND_TZ = pytz.timezone('Europe/Warsaw')


class PolandFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style='{'):
        super().__init__(fmt, datefmt, style)

    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, POLAND_TZ)
        if datefmt:
            s = dt.strftime(datefmt)
        else:
            s = dt.isoformat(timespec='milliseconds')
        return s


class ColorFormatter(logging.Formatter):
    """Dodaje kolorowanie do logów w konsoli."""
    # Format logu z różnymi sekcjami dla lepszej czytelności
    FORMAT = "{time_color}{asctime}{reset} [{level_color}{levelname}{reset}] {name_color}{module}:{funcName}:{lineno}{reset} - {message_color}{message}{reset}"

    # Definicje kolorów dla różnych części logu
    COLOR_CODES = {
        'TIME': Fore.CYAN,  # Kolor dla czasu
        'LEVEL': {
            logging.DEBUG: Fore.BLUE,
            logging.INFO: Fore.GREEN,
            logging.WARNING: Fore.YELLOW,
            logging.ERROR: Fore.RED,
            logging.CRITICAL: Fore.MAGENTA,
        },
        'NAME': Fore.WHITE,  # Biały kolor dla nazwy modułu/funkcji/linii
        'MESSAGE': {
            logging.DEBUG: Fore.LIGHTBLUE_EX,
            logging.INFO: Fore.LIGHTWHITE_EX,
            logging.WARNING: Fore.LIGHTYELLOW_EX,
            logging.ERROR: Fore.LIGHTRED_EX,
            logging.CRITICAL: Fore.LIGHTMAGENTA_EX,
        },
        'RESET': Style.RESET_ALL
    }

    def format(self, record):
        time_color = self.COLOR_CODES['TIME']
        level_color = self.COLOR_CODES['LEVEL'].get(record.levelno, Fore.WHITE)
        name_color = self.COLOR_CODES['NAME']
        message_color = self.COLOR_CODES['MESSAGE'].get(record.levelno, Fore.WHITE)
        reset = self.COLOR_CODES['RESET']

        # Formatowanie logu z kolorami
        log_fmt = self.FORMAT.format(
            time_color=time_color,
            asctime="[{asctime}]",
            reset=reset,
            level_color=level_color,
            levelname="{levelname}",
            name_color=name_color,
            module="{module}",
            funcName="{funcName}",
            lineno="{lineno}",
            message_color=message_color,
            message="{message}"
        )

        # Ustawienie formatera z nowym formatem i stylem '{}'
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S", style='{')
        return formatter.format(record)


def setup_custom_logger(name, log_file, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Ustawienie formatera dla Polski z nowym stylem '{}'
    poland_formatter = PolandFormatter('{asctime} {levelname} {module}:{funcName}:{lineno} - {message}', datefmt='%Y-%m-%d %H:%M:%S %Z')

    # Handlery
    file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
    file_handler.setFormatter(poland_formatter)
    file_handler.setLevel(level)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColorFormatter())
    console_handler.setLevel(level)

    # Dodanie handlerów do loggera
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Upewnij się, że katalog logów istnieje
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Stwórz loggery z nowym formatowaniem
main_logger = setup_custom_logger('[Main]', os.path.join(log_dir, 'main.log'))
scheduler_logger = setup_custom_logger('[Scheduler]', os.path.join(log_dir, 'scheduler.log'))
google_api_logger = setup_custom_logger('[GoogleAPI]', os.path.join(log_dir, 'google_api.log'))
