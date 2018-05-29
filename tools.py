import logging
from string import punctuation

from colorama import Fore, Style

from settings import config


def init_logger():
    logger = logging.getLogger("HackQ")
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(config.get("LOGGING", "FILE"), "w", "utf-8")
    handler.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))
    logger.addHandler(handler)


def color(message, fore):
    return f"{fore}{message}{Style.RESET_ALL}"


colors = Fore
punctuation_to_none = str.maketrans({key: None for key in punctuation})
punctuation_to_space = str.maketrans({key: " " for key in punctuation})
