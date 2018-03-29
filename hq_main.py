import time
from datetime import datetime
from json.decoder import JSONDecodeError

import requests

import settings
from websocket_handler import WebSocketHandler

if settings.get("LOGGING", "Enable"):
    import logging

    # Make sure the logger can handle emojis
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(settings.get("LOGGING", "FILE"), "w", "utf-8")
    handler.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))
    logger.addHandler(handler)


class HQ:
    def __init__(self):
        self.HQ_URL = settings.HQ_URL
        self.HQ_HEADERS = settings.HQ_HEADERS

        self.logging_enabled = settings.get("LOGGING", "Enable")
        self.show_next_info = settings.get("MAIN", "ShowNextShowInfo")
        self.exit_if_offline = settings.get("MAIN", "ExitIfShowOffline")

        self.websocket_handler = WebSocketHandler(self.HQ_HEADERS)

        print("Hack-Q Trivia initialized.")

    def connect(self):
        while True:
            websocket_uri = self.get_websocket_uri()
            if websocket_uri is None:
                continue

            print("Found socket, connecting...")
            websocket_uri = websocket_uri.replace("https", "wss")
            self.websocket_handler.connect(websocket_uri)

    def get_websocket_uri(self):
        try:
            response = requests.get(self.HQ_URL, timeout=1.5, headers=self.HQ_HEADERS).json()
            if self.logging_enabled:
                logging.info(response)
        except JSONDecodeError:
            print("Server response not JSON, retrying...")
            time.sleep(1)
            return

        if "broadcast" not in response or response["broadcast"] is None:
            if "error" in response and response["error"] == "Auth not valid":
                raise RuntimeError("Connection settings invalid")
            else:
                print("Show not on.")
                if self.show_next_info:
                    next_time = datetime.strptime(response["nextShowTime"], "%Y-%m-%dT%H:%M:%S.000Z")
                    now = time.time()
                    offset = datetime.fromtimestamp(now) - datetime.utcfromtimestamp(now)

                    print(f"Next show time: {(next_time + offset).strftime('%Y-%m-%d %I:%M %p')}")
                    print("Prize: " + response["nextShowPrize"])

                if self.exit_if_offline:
                    exit()

            time.sleep(5)  # Don't spam HQ servers
            return None
        else:
            return response["broadcast"]["socketUrl"]


HQ().connect()