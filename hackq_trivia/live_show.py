import json
import logging

from lomond import WebSocket
from unidecode import unidecode

from hackq_trivia.config import config
from hackq_trivia.question import QuestionHandler
from hackq_trivia.tools import color, colors


class LiveShow:
    def __init__(self, headers):
        self.headers = headers
        self.show_question_summary = config.getboolean("LIVE", "ShowQuestionSummary")
        self.show_chat = config.getboolean("LIVE", "ShowChat")

        self.block_chat = False  # Block chat while question is active

        self.logger = logging.getLogger(__name__)

        self.question_handler = QuestionHandler(headers)

    def connect(self, uri):
        websocket = WebSocket(uri)
        for header, value in self.headers.items():
            websocket.add_header(str.encode(header), str.encode(value))

        for event in websocket.connect(ping_rate=5):
            if event.name == "text":
                message = json.loads(event.text)
                self.logger.debug(message)

                if "error" in message and message["error"] == "Auth not valid":
                    raise ConnectionRefusedError("User ID/Bearer invalid. Please check your settings.ini.")
                elif message["type"] == "interaction" and self.show_chat and not self.block_chat:
                    print(f"{message['metadata']['username']}: {message['metadata']['message']}")
                elif message["type"] == "question":
                    question = unidecode(message["question"])
                    choices = [unidecode(choice["text"]) for choice in message["answers"]]

                    print("\n" * 5)
                    print(f"Question {message['questionNumber']} out of {message['questionCount']}")
                    print(color(question, colors.BLUE))
                    print("Choices:", color(", ".join(choices), colors.BLUE))

                    self.question_handler.answer_question(question, choices)

                    self.block_chat = True
                elif self.show_question_summary and message["type"] == "questionSummary":
                    question = unidecode(message["question"])
                    print(f"\nQuestion summary: {color(question, colors.BLUE)}")

                    for answer in message["answerCounts"]:
                        ans_str = unidecode(answer["answer"])

                        print(color(f"{ans_str}:{answer['count']}:{answer['correct']}",
                                    colors.GREEN if answer['correct'] else colors.RED))

                    print(f"{message['advancingPlayersCount']} players advancing")
                    print(f"{message['eliminatedPlayersCount']} players eliminated\n")
                elif self.show_chat and self.block_chat and message["type"] == "questionClosed":
                    self.block_chat = False
                    print("\n" * 5)

        print("Disconnected.")
