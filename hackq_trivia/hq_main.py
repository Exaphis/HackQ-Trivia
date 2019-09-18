import asyncio
import json.decoder
import time
from datetime import datetime

import colorama
import jwt
import nltk
import requests
import logging
import logging.config

from hackq_trivia.config import config
from hackq_trivia.live_show import LiveShow


class BearerException(Exception):
    """Raise when bearer token is invalid/expired"""


class HackQ:
    HQ_URL = f"https://api-quiz.hype.space/shows/schedule?type=hq"

    def __init__(self):
        HackQ.download_nltk_resources()
        colorama.init()

        self.bearer = config.get("CONNECTION", "BEARER")
        self.timeout = config.getfloat("CONNECTION", "Timeout")
        self.show_next_info = config.getboolean("MAIN", "ShowNextShowInfo")
        self.exit_if_offline = config.getboolean("MAIN", "ExitIfShowOffline")
        self.show_bearer_info = config.getboolean("MAIN", "ShowBearerInfo")
        self.headers = {"User-Agent": "Android/1.40.0",
                        "x-hq-client": "Android/1.40.0",
                        "x-hq-country": "US",
                        "x-hq-lang": "en",
                        "x-hq-timezone": "America/New_York",
                        "Authorization": f"Bearer {self.bearer}",
                        "Connection": "close"}

        self.session = requests.Session()
        self.session.headers.update(self.headers)

        self.init_root_logger()
        self.logger = logging.getLogger(__name__)

        # Find local UTC offset
        now = time.time()
        self.local_utc_offset = datetime.fromtimestamp(now) - datetime.utcfromtimestamp(now)

        self.validate_bearer()
        self.logger.info("HackQ-Trivia initialized.\n", extra={"pre": colorama.Fore.GREEN})

    @staticmethod
    def download_nltk_resources():
        for resource in {"stopwords", "averaged_perceptron_tagger", "punkt"}:
            nltk.download(resource, quiet=True)

    @staticmethod
    def init_root_logger():
        import os

        class LogFilterColor(logging.Filter):
            def filter(self, record):
                if "hackq" not in record.name and "__main__" not in record.name:
                    return None

                if not hasattr(record, "pre"):
                    record.pre = ""
                    record.post = ""
                elif not hasattr(record, "post"):
                    record.post = colorama.Style.RESET_ALL

                return record

        log_filename = config.get("LOGGING", "FILE")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if not os.path.isabs(log_filename):
            log_filename = os.path.join(script_dir, log_filename)

        with open(os.path.join(script_dir, "logging_config.json")) as log_conf_file:
            log_conf_dict = json.load(log_conf_file)
            log_conf_dict["handlers"]["fileHandler"]["filename"] = log_filename
            log_conf_dict["filters"]["LogFilterColor"]["()"] = LogFilterColor

            logging.config.dictConfig(log_conf_dict)

    def validate_bearer(self):
        try:
            bearer_info = jwt.decode(self.bearer, verify=False)
        except jwt.exceptions.DecodeError:
            raise BearerException("Bearer invalid. Please check your settings.ini.")

        expiration_time = datetime.utcfromtimestamp(bearer_info["exp"])
        issue_time = datetime.utcfromtimestamp(bearer_info["iat"])

        if datetime.utcnow() > expiration_time:
            raise BearerException("Bearer expired. Please obtain another from your device.")

        if self.show_bearer_info:
            exp_local = expiration_time + self.local_utc_offset
            iat_local = issue_time + self.local_utc_offset

            self.logger.info("Bearer info:")
            self.logger.info(f"    Username: {bearer_info['username']}")
            self.logger.info(f"    Issuing time: {iat_local.strftime('%Y-%m-%d %I:%M %p')}")
            self.logger.info(f"    Expiration time: {exp_local.strftime('%Y-%m-%d %I:%M %p')}")

    async def __connect_show(self, uri):
        async with LiveShow(self.headers) as show:
            await show.connect(uri)

    def connect(self):
        while True:
            websocket_uri = self.get_next_show_info()

            if websocket_uri is not None:
                self.logger.info("Found WebSocket, connecting...\n", extra={"pre": colorama.Fore.GREEN})
                asyncio.run(self.__connect_show(websocket_uri))

    def get_next_show_info(self):
        """
        Gets info of upcoming shows from HQ, prints it out if ShowNextShowInfo is True
        :return: The show's WebSocket URI if it is live, else None
        """
        try:
            response = self.session.get(self.HQ_URL, timeout=self.timeout).json()
            self.logger.debug(response)
        except json.decoder.JSONDecodeError:
            self.logger.info("Server response not JSON, retrying...", extra={"pre": colorama.Fore.RED})
            time.sleep(1)
            return None

        if "error" in response:
            if response["error"] == "Auth not valid":
                raise BearerException("Bearer invalid. Please check your settings.ini.")
            else:
                self.logger.warning(f"Error in server response: {response['error']}")
                time.sleep(1)
                return None

        next_show = response["shows"][0]
        if self.show_next_info:  # If desired, print info of next show
            start_time = datetime.strptime(next_show["startTime"], "%Y-%m-%dT%H:%M:%S.%fZ")
            start_time_local = start_time + self.local_utc_offset

            self.logger.info("Upcoming show:")
            self.logger.info(f"{next_show['display']['title']} - {next_show['display']['summary']}")
            self.logger.info(next_show["display"]["description"])
            if "subtitle" in next_show["display"]:
                self.logger.info(f"Subtitle: {next_show['display']['subtitle']}")
            self.logger.info(f"Prize: ${(next_show['prizeCents'] / 100):0,.2f} {next_show['currency']}")
            self.logger.info(f"Show start time: {start_time_local.strftime('%Y-%m-%d %I:%M %p')}")

        if "live" in next_show:  # Return found WebSocket URI
            return next_show["live"]["socketUrl"].replace("https", "wss")
        else:
            self.logger.info("Show not live.\n", extra={"pre": colorama.Fore.RED})
            if self.exit_if_offline:
                exit()

            time.sleep(5)
            return None


if __name__ == "__main__":
    HackQ().connect()
