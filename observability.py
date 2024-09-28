import logging
from colorama import Fore, Style


class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": Fore.BLUE,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.MAGENTA,
    }

    def format(self, record):
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


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    formatter = ColoredFormatter()
    ch.setFormatter(formatter)

    logger.addHandler(ch)

    return logger


if __name__ == "__main__":
    logger = get_logger("MyLogger")

    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
