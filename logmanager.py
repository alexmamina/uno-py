import logging
import platform

log = logging.getLogger()


class ColorFormatter(logging.Formatter):
    log_format = "%(asctime)s:%(funcName)s:%(lineno)d:%(levelname)s: %(message)s"
    blue = "\x1b[34m"
    green = "\x1b[32m"
    yellow = "\x1b[33m"
    red = "\x1b[31m"
    purple = "\x1b[35m"
    clear = "\x1b[39m"

    FORMATS = {
        logging.DEBUG: blue + log_format + clear,
        logging.INFO: green + log_format + clear,
        logging.WARNING: yellow + log_format + clear,
        logging.ERROR: red + log_format + clear,
        logging.CRITICAL: purple + log_format + clear,
    }

    def format(self, log_line: logging.LogRecord) -> str:
        # Add color to logs on Unix. Otherwise just format information
        if platform.system() != "Windows":
            self.log_format = self.FORMATS.get(log_line.levelno)
        formatter = logging.Formatter(self.log_format)
        return formatter.format(log_line)


def setup_logger(logger: logging.Logger):
    logger.setLevel(logging.DEBUG)
    logging_handler = logging.StreamHandler()
    logging_handler.setFormatter(ColorFormatter())
    logger.addHandler(logging_handler)
