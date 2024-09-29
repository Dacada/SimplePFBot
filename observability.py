import logging
from enum import Enum
from colorama import Fore, Style
from typing import Optional


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

    def get_level(self):
        if self == LogLevel.DEBUG:
            return logging.DEBUG
        if self == LogLevel.INFO:
            return logging.INFO
        if self == LogLevel.WARNING:
            return logging.WARNING
        if self == LogLevel.ERROR:
            return logging.ERROR
        if self == LogLevel.CRITICAL:
            return logging.CRITICAL


class ColoredFormatter(logging.Formatter):
    def __init__(self, support_color):
        self.support_color = support_color

    COLORS = {
        "DEBUG": Fore.BLUE,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.MAGENTA,
    }

    def format(self, record):
        if self.support_color:
            return self.format_color(record)
        else:
            return self.format_nocolor(record)

    def format_nocolor(self, record):
        time = f"{self.formatTime(record, '%Y-%m-%d %H:%M:%S')}"
        padding = 10 - len(record.levelname)
        level = f"[{record.levelname}]" + " " * padding
        logger_name = f"[{record.name}]"
        message = f"{record.getMessage()}"
        return f"{time} {level} {logger_name} {message}"

    def format_color(self, record):
        time = (
            f"{Fore.LIGHTBLACK_EX}"
            f"{self.formatTime(record, '%Y-%m-%d %H:%M:%S')}"
            f"{Style.RESET_ALL}"
        )
        padding = 10 - len(record.levelname)
        level = (
            f"{self.COLORS.get(record.levelname, '')}"
            f"[{record.levelname}]"
            f"{Style.RESET_ALL}" + " " * padding
        )
        logger_name = f"{Fore.CYAN}[{record.name}]{Style.RESET_ALL}"
        message = f"{record.getMessage()}"

        return f"{time} {level} {logger_name} {message}"


def setup_logging(level: LogLevel, file: Optional[str]):
    logger = logging.getLogger()

    level = level.get_level()

    logger.setLevel(level)

    ch = logging.StreamHandler()
    ch.setLevel(level)

    formatter = ColoredFormatter(ch.stream.isatty())
    ch.setFormatter(formatter)

    logger.addHandler(ch)

    if file is not None:
        fh = logging.FileHandler(file)
        fh.setLevel(level)
        fh.setFormatter(ColoredFormatter(False))
        logger.addHandler(fh)


if __name__ == "__main__":
    logger = logging.getLogger("MyLogger")

    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
