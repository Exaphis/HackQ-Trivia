import time
from datetime import datetime
from json.decoder import JSONDecodeError

import jwt
import requests

from hackq_trivia.config import config
from hackq_trivia.live_show import LiveShow


class BearerException(Exception):
    """Raise when bearer token is invalid/expired"""


class HackQ:
    def __init__(self):
        self.BEARER = config.get("CONNECTION", "BEARER")
        self.timeout = config.getfloat("CONNECTION", "Timeout")

        self.HQ_URL = f"https://api-quiz.hype.space/shows/schedule?type=hq"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Android/1.40.0",
                                     "x-hq-client": "Android/1.40.0",
                                     "x-hq-country": "US",
                                     "x-hq-lang": "en",
                                     "x-hq-timezone": "America/New_York",
                                     "Authorization": f"Bearer {self.BEARER}",
                                     "Connection": "close"})

        self.show = LiveShow(self.session.headers)
        self.websocket_uri = None

        self.show_next_info = config.getboolean("MAIN", "ShowNextShowInfo")
        self.exit_if_offline = config.getboolean("MAIN", "ExitIfShowOffline")

        # Setup root logger
        import logging
        import os
        import sys

        log_filename = config.get("LOGGING", "FILE")
        if not os.path.isabs(log_filename):
            log_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), log_filename)

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        fh = logging.FileHandler(log_filename, "w", "utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s", "%m-%d %H:%M"))

        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(logging.Formatter("%(name)-12s: %(levelname)-8s %(message)s"))
        sh.setLevel(logging.INFO)

        root_logger.addHandler(sh)
        root_logger.addHandler(fh)

        self.logger = root_logger

        # Make sure bearer token is valid
        now = time.time()
        self.local_utc_offset = datetime.fromtimestamp(now) - datetime.utcfromtimestamp(now)

        try:
            bearer_info = jwt.decode(self.BEARER, verify=False)
        except jwt.exceptions.DecodeError:
            raise BearerException("Bearer invalid. Please check your settings.ini.")

        expiration_time = datetime.utcfromtimestamp(bearer_info['exp'])
        issue_time = datetime.utcfromtimestamp(bearer_info['iat'])

        if datetime.utcnow() > expiration_time:
            raise BearerException("Bearer expired. Please obtain another from your device.")

        exp_local = expiration_time + self.local_utc_offset
        iat_local = issue_time + self.local_utc_offset

        self.logger.info("Bearer info:")
        self.logger.info(f"    Username: {bearer_info['username']}")
        self.logger.info(f"    Issuing time: {iat_local.strftime('%Y-%m-%d %I:%M %p')}")
        self.logger.info(f"    Expiration time: {exp_local.strftime('%Y-%m-%d %I:%M %p')}")
        self.logger.info("HackQ-Trivia initialized.\n")

    def connect(self):
        while True:
            self.get_show_info()
            if self.websocket_uri is None:
                continue

            self.logger.info("Found socket, connecting...\n")
            self.show.connect(self.websocket_uri)
            self.websocket_uri = None

    def get_show_info(self):
        try:
            response = self.session.get(self.HQ_URL, timeout=self.timeout).json()
            self.logger.debug(response)
        except JSONDecodeError:
            self.logger.info("Server response not JSON, retrying...")
            time.sleep(1)
            return

        if "error" in response and response["error"] == "Auth not valid":
            raise BearerException("Bearer invalid. Please check your settings.ini.")

        next_show = response["shows"][0]
        if self.show_next_info:
            start_time = datetime.strptime(next_show["startTime"], "%Y-%m-%dT%H:%M:%S.%fZ")
            start_time_local = start_time + self.local_utc_offset

            self.logger.info("Upcoming show:")
            self.logger.info(f"{next_show['display']['title']} - {next_show['display']['summary']}")
            self.logger.info(next_show["display"]["description"])
            if "subtitle" in next_show["display"]:
                self.logger.info(f"Subtitle: {next_show['display']['subtitle']}")
            self.logger.info(f"Prize: ${(next_show['prizeCents'] / 100):0,.2f} {next_show['currency']}")
            self.logger.info(f"Show start time: {start_time_local.strftime('%Y-%m-%d %I:%M %p')}")

        if "live" in next_show:
            self.websocket_uri = next_show["live"]["socketUrl"]
        else:
            self.logger.info("Show not live.\n")
            self.websocket_uri = None
            if self.exit_if_offline:
                exit()

            time.sleep(5)


if __name__ == "__main__":
    HackQ().connect()
