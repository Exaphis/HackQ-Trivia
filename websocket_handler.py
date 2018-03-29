import json
import logging

from lomond import WebSocket

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

        for event in websocket.connect(ping_rate=5, ping_timeout=5):
            if event.name == "text":
                message = json.loads(event.text)
                print(message)
                logging.info(str(message))