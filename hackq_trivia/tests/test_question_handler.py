import unittest

from hackq_trivia.question_handler import QuestionHandler


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.qh = QuestionHandler({})

    def test_find_keywords_consecutive_capitals(self):
        self.assertEqual(self.qh.find_keywords("Do you love Nathaniel Hawthorne's books?"),
                         ["love", "Nathaniel Hawthorne's", "books"])

    def test_find_keywords_quotations(self):
        self.assertEqual(self.qh.find_keywords('I do love "The Scarlet Letter".'),
                         ["love", "The Scarlet Letter"])


if __name__ == '__main__':
    unittest.main()
