from colorama import Fore, Style
colors = Fore


def color(message, fore):
    return f"{fore}{message}{Style.RESET_ALL}"
