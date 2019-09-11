import asyncio
import logging
from operator import itemgetter

import aiohttp
import googleapiclient.discovery

from hackq_trivia.config import config


class Searcher:
    def __init__(self, headers):
        self.timeout = config.getfloat("CONNECTION", "Timeout")
        self.cse_id = config.get("CONNECTION", "GoogleCseId")
        api_key = config.get("CONNECTION", "GoogleApiKey")

        self.session = aiohttp.ClientSession(headers=headers)
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

