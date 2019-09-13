import asyncio
import logging
from html import unescape
from operator import itemgetter

import aiohttp
import googleapiclient.discovery
from bs4 import BeautifulSoup
from unidecode import unidecode

from hackq_trivia.config import config


class Searcher:
    HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:58.0) Gecko/20100101 Firefox/58.0"}

    def __init__(self):
        self.timeout = config.getfloat("CONNECTION", "Timeout")
        self.cse_id = config.get("CONNECTION", "GoogleCseId")
        api_key = config.get("CONNECTION", "GoogleApiKey")

        self.session = aiohttp.ClientSession(headers=Searcher.HEADERS)
        self.search_service = googleapiclient.discovery.build("customsearch", "v1", developerKey=api_key)

        self.logger = logging.getLogger(__name__)

    async def fetch(self, url):
        try:
            async with self.session.get(url, timeout=self.timeout) as response:
                return await response.text()
        except Exception:
            self.logger.error(f"Server timeout/error to {url}")
            return ""

    async def fetch_multiple(self, urls):
        tasks = [asyncio.ensure_future(self.fetch(url)) for url in urls]
        responses = await asyncio.gather(*tasks)
        return responses

    async def close(self):
        await self.session.close()

    def get_google_links(self, query, num_results):
        res = self.search_service.cse().list(q=query, cx=self.cse_id, num=num_results).execute()
        return list(map(itemgetter("link"), res["items"]))

    @staticmethod
    def clean_html(html):
        return unidecode(unescape(BeautifulSoup(html, features="html.parser").get_text()))
