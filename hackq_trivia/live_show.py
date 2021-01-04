import json
import logging

import aiohttp
import colorama
from unidecode import unidecode

from hackq_trivia.config import config
from hackq_trivia.question_handler import QuestionHandler


class LiveShow:
    async def __aenter__(self):
        self.question_handler = QuestionHandler()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.question_handler.close()

    def __init__(self, headers):
        self.headers = headers
        self.show_question_summary = config.getboolean('LIVE', 'ShowQuestionSummary')
        self.show_chat = config.getboolean('LIVE', 'ShowChat')
        self.block_chat = False  # Block chat while question is active
        self.logger = logging.getLogger(__name__)
        self.logger.info('LiveShow initialized.')

    async def connect(self, uri):
        session = aiohttp.ClientSession()

        rejoin = True
        while rejoin:
            async with session.ws_connect(uri, headers=self.headers, heartbeat=5) as ws:
                async for msg in ws:
                    # suppress incorrect type warning for msg in PyCharm
                    rejoin = await self.handle_msg(msg)  # noqa

                    if rejoin:
                        break

        self.logger.info('Disconnected.')

    async def handle_msg(self, msg):
        """
        Handles WebSocket frame received from HQ server.
        :param msg: Message received by aiohttp
        :return: True if the WS connection should be rejoined, False otherwise
        """
        if msg.type == aiohttp.WSMsgType.TEXT:
            message = json.loads(msg.data)
            self.logger.debug(message)

            if 'error' in message and message['error'] == 'Auth not valid':
                raise ConnectionRefusedError('User ID/Bearer invalid. Please check your settings.ini.')

            message_type = message['type']

            if message_type == 'broadcastEnded' and \
               message['reason'] == 'You are no longer in the game. Please join again.':
                return True

            elif message_type == 'interaction' and self.show_chat and not self.block_chat:
                self.logger.info(f'{message["metadata"]["username"]}: {message["metadata"]["message"]}')
                
            elif message_type == 'question':
                question = unidecode(message['question'])
                choices = [unidecode(choice['text']) for choice in message['answers']]

                self.logger.info('\n' * 5)
                self.logger.info(f'Question {message["questionNumber"]} out of {message["questionCount"]}')
                self.logger.info(question, extra={"pre": colorama.Fore.BLUE})
                self.logger.info(f'Choices: {", ".join(choices)}', extra={'pre': colorama.Fore.BLUE})

                await self.question_handler.answer_question(question, choices)

                self.block_chat = True
                
            elif message_type == 'questionSummary' and self.show_question_summary:
                question = unidecode(message['question'])
                self.logger.info(f'Question summary: {question}', extra={'pre': colorama.Fore.BLUE})

                for answer in message['answerCounts']:
                    ans_str = unidecode(answer['answer'])

                    self.logger.info(f'{ans_str}:{answer["count"]}:{answer["correct"]}',
                                     extra={'pre': colorama.Fore.GREEN if answer['correct'] else colorama.Fore.RED})

                self.logger.info(f'{message["advancingPlayersCount"]} players advancing')
                self.logger.info(f'{message["eliminatedPlayersCount"]} players eliminated\n')
                
            elif message_type == 'questionClosed' and self.block_chat:
                self.block_chat = False
                if self.show_chat:
                    self.logger.info('\n' * 5)

        return False
