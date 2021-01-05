import json
import unittest
from urllib.parse import urlparse
import warnings

from hackq_trivia.searcher import Searcher


class SearcherFetchTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self._searcher = Searcher()

    async def asyncTearDown(self) -> None:
        await self._searcher.close()

    async def test_fetch_single(self):
        resp = await self._searcher.fetch('http://httpbin.org/user-agent')
        resp = json.loads(resp)
        self.assertEqual(resp['user-agent'], Searcher.HEADERS['User-Agent'])

    async def test_fetch_multiple(self):
        resps = await self._searcher.fetch_multiple(['http://httpbin.org/user-agent'] * 5)
        self.assertEqual(len(resps), 5)
        for resp in resps:
            resp = json.loads(resp)
            self.assertEqual(resp['user-agent'], Searcher.HEADERS['User-Agent'])

    async def test_fetch_error(self):
        with self.assertLogs() as log_cm:
            await self._searcher.fetch('http://aaaa.aaa')
        self.assertIn('ERROR:hackq_trivia.searcher:Server error to http://aaaa.aaa', log_cm.output)

    async def test_fetch_delay(self):
        max_timeout = self._searcher.timeout
        fail_url = f'http://httpbin.org/delay/{max_timeout + 1}'

        with self.assertLogs() as log_cm:
            resps = await self._searcher.fetch_multiple(['http://httpbin.org/delay/0', fail_url])
            self.assertTrue(resps[0])
            self.assertFalse(resps[1])

        self.assertEqual([f'ERROR:hackq_trivia.searcher:Server timeout to {fail_url}'], log_cm.output)


class SearcherSearchEngineTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self._searcher = Searcher()

    async def asyncTearDown(self) -> None:
        await self._searcher.close()

    def setUp(self) -> None:
        # google-api-python-client raises benign ResourceWarnings, ignore for now
        warnings.simplefilter('ignore', ResourceWarning)

    async def test_get_google_links(self):
        links = await self._searcher.get_google_links('test test test test', 5)
        print('Google links:')
        for link in links:
            print(link)
            parsed = urlparse(link)
            self.assertTrue(all((parsed.scheme, parsed.netloc)))
        self.assertEqual(len(links), 5)

    async def test_get_bing_links(self):
        links = await self._searcher.get_bing_links('test test test test', 5)
        print('Bing links:')
        for link in links:
            print(link)
            parsed = urlparse(link)
            self.assertTrue(all((parsed.scheme, parsed.netloc)))
        self.assertEqual(len(links), 5)


if __name__ == '__main__':
    unittest.main()
