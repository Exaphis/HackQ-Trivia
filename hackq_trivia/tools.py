from colorama import Fore, Style


def color(message, fore):
    return f"{fore}{message}{Style.RESET_ALL}"


colors = Fore
