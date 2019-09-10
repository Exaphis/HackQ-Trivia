import asyncio
import json
import unittest

from hackq_trivia.searcher import Searcher


class SearcherTest(unittest.TestCase):
    def setUp(self) -> None:
        self.loop = asyncio.get_event_loop()

        self.HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:58.0) Gecko/20100101 Firefox/58.0"}
        self.searcher = Searcher(self.HEADERS, self.loop)

    def tearDown(self) -> None:
        self.loop.run_until_complete(self.searcher.close())

    def test_fetch(self):
        resp = self.loop.run_until_complete(self.searcher.fetch("http://httpbin.org/user-agent"))
        resp = json.loads(resp)
        self.assertEqual(resp["user-agent"], self.HEADERS["User-Agent"])

    def test_fetch_multiple(self):
        resps = self.loop.run_until_complete(self.searcher.fetch_multiple(["http://httpbin.org/user-agent"] * 5))
        for resp in resps:
            resp = json.loads(resp)
            self.assertEqual(resp["user-agent"], self.HEADERS["User-Agent"])

    def test_fetch_error(self):
        with self.assertLogs() as cm:
            self.loop.run_until_complete(self.searcher.fetch("http://aaaa.aaa"))
        self.assertEqual(cm.output, ['ERROR:hackq_trivia.searcher:Server timeout/error to http://aaaa.aaa'])


if __name__ == '__main__':
    unittest.main()
