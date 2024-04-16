import logging
import platform
from datetime import datetime

LOG_FORMAT = "%(asctime)s:%(funcName)s:%(lineno)d:%(levelname)s: %(message)s"


class ColorFormatter(logging.Formatter):
    blue = "\x1b[34m"
    green = "\x1b[32m"
    yellow = "\x1b[33m"
    red = "\x1b[31m"
    purple = "\x1b[35m"
    clear = "\x1b[39m"

    FORMATS = {
        logging.DEBUG: blue + LOG_FORMAT + clear,
        logging.INFO: green + LOG_FORMAT + clear,
        logging.WARNING: yellow + LOG_FORMAT + clear,
        logging.ERROR: red + LOG_FORMAT + clear,
        logging.CRITICAL: purple + LOG_FORMAT + clear,
    }

    def format(self, log_line: logging.LogRecord) -> str:
        # Add color to logs on Unix. Otherwise just format information
        if platform.system() != "Windows":
            self.log_format = self.FORMATS.get(log_line.levelno)
        formatter = logging.Formatter(self.log_format)
        return formatter.format(log_line)


def setup_logger(logger: logging.Logger, user: str):
    logger.setLevel(logging.DEBUG)
    logging_handler = logging.StreamHandler()
    logging_handler.setFormatter(ColorFormatter())
    logger.addHandler(logging_handler)

    timestamp = datetime.now().strftime('%d-%m-%Y_%H-%M')
    file_handler = logging.FileHandler(f"{user}-logs-{timestamp}.log")
    # Set the format for the logs, but don't use the ColorFormatter as colors aren't saved to files
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(file_handler)
