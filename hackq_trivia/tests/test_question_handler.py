import asyncio
import unittest

from hackq_trivia.question_handler import QuestionHandler


class MyTestCase(unittest.TestCase):
    async def setUpAsync(self):
        self.qh = QuestionHandler()

    def setUp(self) -> None:
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.setUpAsync())

    def tearDown(self) -> None:
        self.loop.run_until_complete(self.qh.close())

    def test_find_keywords_consecutive_capitals(self):
        self.assertEqual(self.qh.find_keywords("Do you love Nathaniel Hawthorne's books?"),
                         ["love", "Nathaniel Hawthorne's", "books"])

    def test_find_keywords_quotations(self):
        self.assertEqual(self.qh.find_keywords('I do love "The Scarlet Letter".'),
                         ["love", "The Scarlet Letter"])

    def test_answer_question(self):
        self.loop.run_until_complete(self.qh.answer_question("What is the word for a landmass like Florida that is "
                                                             "surrounded on three sides by water?",
                                                             ["Peninsula", "Piñata", "Trifecta"]))


if __name__ == '__main__':
    unittest.main()
