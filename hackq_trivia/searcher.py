import asyncio
import logging
import operator
from html import unescape

import aiohttp
import bs4
import googleapiclient.discovery
from unidecode import unidecode

from hackq_trivia.config import config


class Searcher:
    HEADERS = {"User-Agent": "HQbot"}

    def __init__(self):
        self.timeout = config.getfloat("CONNECTION", "Timeout")
        self.cse_id = config.get("CONNECTION", "GoogleCseId")
        api_key = config.get("CONNECTION", "GoogleApiKey")
        self.search_service = googleapiclient.discovery.build("customsearch", "v1", developerKey=api_key)
        self.session = aiohttp.ClientSession(headers=Searcher.HEADERS)
        self.logger = logging.getLogger(__name__)

    async def fetch(self, url):
        try:
            async with self.session.get(url, timeout=self.timeout) as response:
                return await response.text()
        except Exception as e:
            self.logger.error(f"Server timeout/error to {url}")
            self.logger.error(e)
            return ""

    async def fetch_multiple(self, urls):
        tasks = [asyncio.create_task(self.fetch(url)) for url in urls]
        responses = await asyncio.gather(*tasks)
        return responses

    async def close(self):
        await self.session.close()

    def get_google_links(self, query, num_results):
        response = self.search_service.cse().list(q=query, cx=self.cse_id, num=num_results).execute()
        return list(map(operator.itemgetter("link"), response["items"]))

    @staticmethod
    def html_to_visible_text(html):
        soup = bs4.BeautifulSoup(html, features="html.parser")
        for s in soup(["style", "script", "[document]", "head", "title"]):
            s.extract()

        return unidecode(unescape(soup.get_text())).lower()
