import unittest
import logging

from hackq_trivia.hq_main import init_root_logger


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        init_root_logger()
        self.logger = logging.getLogger(__name__)

    def test_emojis(self):
        self.logger.info("👁 👃🏾👄👁")


if __name__ == "__main__":
    unittest.main()
