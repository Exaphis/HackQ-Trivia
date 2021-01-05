import asyncio
import logging
from html import unescape
from typing import Iterable, List

import aiohttp
import bs4
from unidecode import unidecode

from hackq_trivia.config import config


class InvalidSearchServiceError(Exception):
    """Raise when search service specified in config is not recognized."""


class Searcher:
    HEADERS = {'User-Agent': 'HQbot'}
    BING_ENDPOINT = 'https://api.bing.microsoft.com/v7.0/search'
    GOOGLE_ENDPOINT = 'https://www.googleapis.com/customsearch/v1'

    def __init__(self):
        # TODO: persistent aiohttp ClientSession
        self.timeout = config.getfloat('CONNECTION', 'Timeout')
        self.search_service = config.get('SEARCH', 'Service')

        bing_api_key = config.get('SEARCH', 'BingApiKey')
        self.bing_headers = {'Ocp-Apim-Subscription-Key': bing_api_key}

        self.google_cse_id = config.get('SEARCH', 'GoogleCseId')
        self.google_api_key = config.get('SEARCH', 'GoogleApiKey')

        if self.search_service == 'Bing':
            self.search_func = self.get_bing_links
        elif self.search_service == 'Google':
            self.search_func = self.get_google_links
        else:
            raise InvalidSearchServiceError(f'Search service type {self.search_service} was not recognized.')

        client_timeout = aiohttp.ClientTimeout(total=self.timeout)
        self.session = aiohttp.ClientSession(headers=Searcher.HEADERS, timeout=client_timeout)
        self.logger = logging.getLogger(__name__)

    async def fetch(self, url: str) -> str:
        try:
            async with self.session.get(url, timeout=self.timeout) as response:
                return await response.text()
        except asyncio.TimeoutError:
            self.logger.error(f'Server timeout to {url}')
        except Exception as e:
            self.logger.error(f'Server error to {url}')
            self.logger.error(e)

        return ""

    # no typing info for return value because https://github.com/python/typeshed/issues/2652
    async def fetch_multiple(self, urls: Iterable[str]):
        coroutines = [self.fetch(url) for url in urls]
        responses = await asyncio.gather(*coroutines)
        return responses

    async def close(self) -> None:
        await self.session.close()

    async def get_search_links(self, query: str, num_results: int) -> List[str]:
        return await self.search_func(query, num_results)

    async def get_google_links(self, query: str, num_results: int) -> List[str]:
        async with aiohttp.ClientSession() as session:
            search_params = {'key': self.google_api_key,
                             'cx': self.google_cse_id,
                             'q': query,
                             'num': num_results}

            async with session.get(self.GOOGLE_ENDPOINT, params=search_params) as resp:
                resp_status = resp.status
                resp_data = await resp.json()

                if resp_status != 200:
                    logging.error(f'Google search failed with status code {resp_status}')
                    logging.error(resp_data)
                    return []

        self.logger.debug(f'google: {query}, n={num_results}')
        self.logger.debug(resp_data)

        return [item['link'] for item in resp_data['items']]

    async def get_bing_links(self, query: str, num_results: int) -> List[str]:
        async with aiohttp.ClientSession(headers=self.bing_headers) as session:
            # why does Bing consistently deliver 1 fewer result than requested?
            search_params = {'q': query, 'count': num_results + 1}

            async with session.get(self.BING_ENDPOINT, params=search_params) as resp:
                resp_status = resp.status
                resp_data = await resp.json()

                if resp_status != 200:
                    logging.error(f'Bing search failed with status code {resp_status}')
                    logging.error(resp_data)
                    return []

        self.logger.debug(f'bing: {query}, n={num_results}')
        self.logger.debug(resp_data)

        return [item['url'] for item in resp_data['webPages']['value']]

    @staticmethod
    def html_to_visible_text(html):
        soup = bs4.BeautifulSoup(html, features='html.parser')
        for s in soup(['style', 'script', '[document]', 'head', 'title']):
            s.extract()

        return unidecode(unescape(soup.get_text())).lower()
