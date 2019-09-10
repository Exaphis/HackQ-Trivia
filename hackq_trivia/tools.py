from string import punctuation

from colorama import Fore, Style


def color(message, fore):
    return f"{fore}{message}{Style.RESET_ALL}"


colors = Fore
punctuation_to_none = str.maketrans({key: None for key in punctuation})
punctuation_to_space = str.maketrans({key: " " for key in punctuation})
