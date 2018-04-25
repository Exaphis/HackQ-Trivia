import json
import logging

from colorama import Fore, Style
from lomond import WebSocket
from unidecode import unidecode

import settings


class WebSocketHandler:
    def __init__(self, headers):
        self.headers = headers
        self.logging_enabled = settings.get("LOGGING", "Enable")
        self.log_chat = settings.get("LOGGING", "LogChat")

    def connect(self, uri):
        websocket = WebSocket(uri)
        for header, value in self.headers.items():
            websocket.add_header(str.encode(header), str.encode(value))

        for event in websocket.connect(ping_rate=5):
            if event.name == "text":
                message = json.loads(event.text)

                if "error" in message and message["error"] == "Auth not valid":
                    logging.debug(message)
                    raise ConnectionRefusedError("User ID/Bearer invalid. Please check your settings.ini.")
                elif message["type"] == "question":
                    logging.debug(message)
                    question = unidecode(message["question"])
                    choices = [unidecode(choice["text"]) for choice in message["answers"]]

                    print("\n"*5)
                    print("Question detected.")
                    print(f"Question {message['questionNumber']} out of {message['questionCount']}")
                    print(f"{Fore.CYAN}{question}\nChoices: {', '.join(choices)}{Style.RESET_ALL}\n")
                elif self.logging_enabled and self.log_chat and message["type"] == "interaction":
                    logging.debug(message)
