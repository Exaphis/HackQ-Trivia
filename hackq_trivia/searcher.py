import asyncio
import logging

import aiohttp

from hackq_trivia.config import config


class Searcher:
    def __init__(self, headers, event_loop):
        self.timeout = config.getfloat("CONNECTION", "Timeout")

        self.session = aiohttp.ClientSession(headers=headers, loop=event_loop)

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
