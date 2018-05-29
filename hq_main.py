import logging
import time
from datetime import datetime
from json.decoder import JSONDecodeError

import requests

from settings import config
from tools import init_logger
from websocket import WebSocketHandler

init_logger()


class HackQ:
    def __init__(self):
        self.BEARER = config.get("CONNECTION", "BEARER")
        self.HQ_URL = f"https://api-quiz.hype.space/shows/now?type="
        self.HQ_HEADERS = {"Authorization": f"Bearer {self.BEARER}",
                           "x-hq-client": "Android/1.3.0"}

        self.timeout = config.getfloat("CONNECTION", "Timeout")

        self.show_next_info = config.getboolean("MAIN", "ShowNextShowInfo")
        self.exit_if_offline = config.getboolean("MAIN", "ExitIfShowOffline")

        self.websocket_handler = WebSocketHandler(self.HQ_HEADERS)

        self.logger = logging.getLogger("HackQ")

        print("HackQ Trivia initialized.")

    def connect(self):
        while True:
            websocket_uri = self.get_websocket_uri()
            if websocket_uri is None:
                continue

            print("Found socket, connecting...\n")
            websocket_uri = websocket_uri.replace("https", "wss")
            self.websocket_handler.connect(websocket_uri)

    def get_websocket_uri(self):
        try:
            response = requests.get(self.HQ_URL, timeout=self.timeout, headers=self.HQ_HEADERS).json()
            self.logger.debug(response)
        except JSONDecodeError:
            print("Server response not JSON, retrying...")
            time.sleep(1)
            return

        if "broadcast" not in response or response["broadcast"] is None:
            if "error" in response and response["error"] == "Auth not valid":
                raise ConnectionRefusedError("Bearer invalid. Please check your settings.ini.")
            else:
                print("Show not on.")
                if self.show_next_info:
                    next_time = datetime.strptime(response["nextShowTime"], "%Y-%m-%dT%H:%M:%S.000Z")
                    now = time.time()
                    offset = datetime.fromtimestamp(now) - datetime.utcfromtimestamp(now)

                    print(f"Next show time: {(next_time + offset).strftime('%Y-%m-%d %I:%M %p')}")
                    print(f"Prize: {response['nextShowPrize']}")

                if self.exit_if_offline:
                    exit()

            time.sleep(5)  # Don't spam HQ servers
            return None
        else:
            return response["broadcast"]["socketUrl"]


HackQ().connect()
