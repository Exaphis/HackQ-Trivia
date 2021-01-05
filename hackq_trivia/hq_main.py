import asyncio
import json.decoder
import time
from typing import Optional
from datetime import datetime
import os

import colorama
import jwt
import nltk
import requests
import logging
import logging.config

from hackq_trivia.config import config
from hackq_trivia.live_show import LiveShow


class BearerError(Exception):
    """Raise when bearer token is invalid/expired"""


def next_available_name(base_name: str) -> str:
    """
    Finds lowest available file name using .format() to insert numbers (starts at 1).
    :param base_name: File name containing format placeholder ({})
    :return: File name with lowest number inserted.
    """
    num = 1
    curr_name = base_name.format(num)
    while os.path.exists(curr_name):
        num += 1
        curr_name = base_name.format(num)

    return curr_name


def init_root_logger() -> None:
    import os

    class LogFilterColor(logging.Filter):
        def filter(self, record):
            if 'hackq' not in record.name and '__main__' not in record.name:
                return None

            if not hasattr(record, 'pre'):
                record.pre = ''
                record.post = ''
            elif not hasattr(record, 'post'):
                record.post = colorama.Style.RESET_ALL

            return record

    log_filename = config.get('LOGGING', 'File')
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isabs(log_filename):
        log_filename = os.path.join(script_dir, log_filename)

    inc_filenames = config.getboolean('LOGGING', 'IncrementFileNames')
    # check if name contains format string placeholder
    if inc_filenames and log_filename.format(0) == log_filename:
        inc_filenames = False
    if inc_filenames:
        log_filename = next_available_name(log_filename)

    with open(os.path.join(script_dir, 'logging_config.json')) as log_conf_file:
        log_conf_dict = json.load(log_conf_file)
        log_conf_dict['handlers']['fileHandler']['filename'] = log_filename
        log_conf_dict['filters']['LogFilterColor']['()'] = LogFilterColor

        logging.config.dictConfig(log_conf_dict)


def download_nltk_resources() -> None:
    for resource in ('stopwords', 'averaged_perceptron_tagger', 'punkt'):
        nltk.download(resource, raise_on_error=True)


class HackQ:
    HQ_SCHEDULE_URL = f'https://api-quiz.hype.space/shows/schedule?type=hq'

    def __init__(self):
        if config.getboolean('MAIN', 'DownloadNLTKResources'):
            download_nltk_resources()
        colorama.init()

        self.bearer = config.get('CONNECTION', 'Bearer')
        self.timeout = config.getfloat('CONNECTION', 'Timeout')
        self.show_next_info = config.getboolean('MAIN', 'ShowNextShowInfo')
        self.exit_if_offline = config.getboolean('MAIN', 'ExitIfShowOffline')
        self.show_bearer_info = config.getboolean('MAIN', 'ShowBearerInfo')
        self.headers = {'User-Agent': 'Android/1.40.0',
                        'x-hq-client': 'Android/1.40.0',
                        'x-hq-country': 'US',
                        'x-hq-lang': 'en',
                        'x-hq-timezone': 'America/New_York',
                        'Authorization': f'Bearer {self.bearer}'}

        self.session = requests.Session()
        self.session.headers.update(self.headers)

        init_root_logger()
        self.logger = logging.getLogger(__name__)

        # Find local UTC offset
        now = time.time()
        self.local_utc_offset = datetime.fromtimestamp(now) - datetime.utcfromtimestamp(now)

        self.validate_bearer()
        self.logger.info('HackQ-Trivia initialized.\n', extra={'pre': colorama.Fore.GREEN})

    def validate_bearer(self) -> None:
        try:
            # verify and options args exist to support all versions of pyjwt
            # iat/exp is not checked by pyjwt if verify_signature is False
            bearer_info = jwt.decode(self.bearer, verify=False,
                                     options={'verify_signature': False})
        except jwt.exceptions.DecodeError as e:
            raise BearerError('Bearer token decode failed. Please check your settings.ini.') from e

        expiration_time = datetime.utcfromtimestamp(bearer_info['exp'])
        issue_time = datetime.utcfromtimestamp(bearer_info['iat'])

        if datetime.utcnow() > expiration_time:
            raise BearerError('Bearer token expired. Please obtain another from your device.')

        if self.show_bearer_info:
            exp_local = expiration_time + self.local_utc_offset
            iat_local = issue_time + self.local_utc_offset

            self.logger.info('Bearer token details:')
            self.logger.info(f'    Username: {bearer_info["username"]}')
            self.logger.info(f'    Issuing time: {iat_local.strftime("%Y-%m-%d %I:%M %p")}')
            self.logger.info(f'    Expiration time: {exp_local.strftime("%Y-%m-%d %I:%M %p")}')

    async def __connect_show(self, uri) -> None:
        async with LiveShow(self.headers) as show:
            await show.connect(uri)

    def connect(self) -> None:
        while True:
            try:
                websocket_uri = self.get_next_show_info()

                if websocket_uri is not None:
                    self.logger.info('Found WebSocket, connecting...\n', extra={'pre': colorama.Fore.GREEN})
                    self.logger.debug(websocket_uri)
                    asyncio.run(self.__connect_show(websocket_uri))
            except KeyboardInterrupt:
                self.logger.error('Interrupted, exiting...')
                break

    def get_next_show_info(self) -> Optional[str]:
        """
        Gets info of upcoming shows from HQ, prints it out if ShowNextShowInfo is True
        :return: The show's WebSocket URI if it is live, else None
        """
        try:
            response = self.session.get(self.HQ_SCHEDULE_URL, timeout=self.timeout).json()
            self.logger.debug(response)
        except json.decoder.JSONDecodeError:
            self.logger.info('Server response not JSON, retrying...', extra={'pre': colorama.Fore.RED})
            time.sleep(1)
            return None

        if 'error' in response:
            if response['error'] == 'Auth not valid':
                raise BearerError('Bearer token rejected. Please check your settings.ini or use a VPN.')
            else:
                self.logger.warning(f'Error in server response: {response["error"]}')
                time.sleep(1)
                return None

        next_show = response['shows'][0]
        if self.show_next_info:  # If desired, print info of next show
            start_time = datetime.strptime(next_show['startTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
            start_time_local = start_time + self.local_utc_offset

            self.logger.info('Upcoming show:')
            self.logger.info(f'{next_show["display"]["title"]} - {next_show["display"]["summary"]}')
            self.logger.info(next_show['display']['description'])
            if 'subtitle' in next_show['display']:
                self.logger.info(f'Subtitle: {next_show["display"]["subtitle"]}')
            self.logger.info(f'Prize: ${(next_show["prizeCents"] / 100):0,.2f} {next_show["currency"]}')
            self.logger.info(f'Show start time: {start_time_local.strftime("%Y-%m-%d %I:%M %p")}')

        if 'live' in next_show:  # Return found WebSocket URI
            return next_show['live']['socketUrl'].replace('https', 'wss')
        else:
            self.logger.info('Show not live.\n', extra={'pre': colorama.Fore.RED})
            if self.exit_if_offline:
                exit()

            time.sleep(5)
            return None


if __name__ == '__main__':
    HackQ().connect()
