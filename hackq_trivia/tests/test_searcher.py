import asyncio
import json
import unittest
from urllib.parse import urlparse

from hackq_trivia.searcher import Searcher


class SearcherTest(unittest.TestCase):
    async def setUpAsync(self):
        self.searcher = Searcher()

    def setUp(self) -> None:
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.setUpAsync())

    def tearDown(self) -> None:
        self.loop.run_until_complete(self.searcher.close())

    def test_fetch_single(self):
        resp = self.loop.run_until_complete(self.searcher.fetch("http://httpbin.org/user-agent"))
        resp = json.loads(resp)
        self.assertEqual(resp["user-agent"], Searcher.HEADERS["User-Agent"])

    def test_fetch_multiple(self):
        resps = self.loop.run_until_complete(self.searcher.fetch_multiple(["http://httpbin.org/user-agent"] * 5))
        for resp in resps:
            resp = json.loads(resp)
            self.assertEqual(resp["user-agent"], Searcher.HEADERS["User-Agent"])

    def test_fetch_error(self):
        with self.assertLogs() as cm:
            self.loop.run_until_complete(self.searcher.fetch("http://aaaa.aaa"))
        self.assertEqual(cm.output, ['ERROR:hackq_trivia.searcher:Server timeout/error to http://aaaa.aaa'])

    def test_get_google_links(self):
        links = self.searcher.get_google_links("test test test test", 5)
        self.assertEqual(len(links), 5)
        for link in links:
            print(link)
            parsed = urlparse(link)
            self.assertTrue(all((parsed.scheme, parsed.netloc)))


if __name__ == '__main__':
    unittest.main()
