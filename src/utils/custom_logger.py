import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
import pytz
from rich.logging import RichHandler
from rich.console import Console
from rich.theme import Theme
from rich.traceback import install

# Instalacja obsługi wyjątków Rich
install(show_locals=True)

# Definicja strefy czasowej dla Polski
POLAND_TZ = pytz.timezone('Europe/Warsaw')

# Niestandardowy motyw kolorów
custom_theme = Theme({
    "info": "bold green",
    "warning": "bold yellow",
    "error": "bold red",
    "critical": "bold white on red",
    "debug": "cyan",
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
    file_formatter = PolandFormatter(
        '{asctime} {levelname:<8} {name:<15} {module}:{funcName}:{lineno:<4} - {message}',
        datefmt='%Y-%m-%d %H:%M:%S %Z',
        style='{'
    )

    # Handler dla pliku
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(level)

    # Rich handler dla konsoli
    console_handler = RichHandler(
        console=console,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        show_time=True,
        show_path=True
    )
    console_handler.setLevel(level)

    # Dodanie handlerów do loggera
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# Upewnij się, że katalog logów istnieje
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Stwórz loggery
main_logger = setup_custom_logger('Main', os.path.join(log_dir, 'main.log'))
scheduler_logger = setup_custom_logger('Scheduler', os.path.join(log_dir, 'scheduler.log'))
google_api_logger = setup_custom_logger('GoogleAPI', os.path.join(log_dir, 'google_api.log'))

# Przykłady użycia
if __name__ == "__main__":
    main_logger.debug("To jest wiadomość debugowa")
    main_logger.info("To jest informacja")
    main_logger.warning("To jest ostrzeżenie")
    main_logger.error("To jest błąd")
    main_logger.critical("To jest krytyczny błąd")

    scheduler_logger.info("Zadanie zaplanowane")
    google_api_logger.error("Błąd połączenia z API Google")

    try:
        1 / 0
    except Exception as e:
        main_logger.exception("Wystąpił nieoczekiwany błąd")