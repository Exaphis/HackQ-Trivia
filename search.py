import asyncio
import html
import re
from concurrent.futures import CancelledError

import aiohttp
import async_timeout
from bs4 import BeautifulSoup
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer

STOP = set(stopwords.words("english"))
tokenizer = RegexpTokenizer(r"\w+")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:58.0) Gecko/20100101 Firefox/58.0",
           "Accept": "*/*",
           "Accept-Language": "en-US,en;q=0.5",
           "Accept-Encoding": "gzip, deflate"}
GOOGLE_URL = "https://www.google.com/search?q={}&ie=utf-8&oe=utf-8&client=firefox-b-1-ab"


def find_keywords(words):
    """
    Returns the list of words given without stopwords.
    :param words: List of words
    :return: Words without stopwords
    """
    return [w for w in tokenizer.tokenize(words.lower()) if w not in STOP]


def get_google_links(page, num_results):
    soup = BeautifulSoup(page, "html.parser")
    results = soup.findAll("h3", {"class": "r"})
    links = [str(r.find("a")["href"]) for r in results]
    links = list(dict.fromkeys(links))  # Remove duplicates while preserving order
    return links[:num_results]


async def search_google(question, num_results):
    """
    Returns num_results urls from a google search of question.
    :param question: Question to search
    :param num_results: Number of results to return
    :return: List of length num_results of urls retrieved from the search
    """
    # Could use Google's Custom Search API here, limit of 100 queries per day
    # result = service.cse().list(q=question, cx=CSE_ID, num=num_results).execute()
    # return result["items"]

    pages = await get_texts([GOOGLE_URL.format(question)], clean=False, timeout=5)
    return get_google_links(pages[0], num_results)


async def multiple_search(questions, num_results):
    queries = list(map(GOOGLE_URL.format, questions))
    pages = await get_texts(queries, clean=False, timeout=5)
    link_list = [get_google_links(page, num_results) for page in pages]
    return link_list


def clean_html(html):
    """
    Copied from NLTK package.
    Remove HTML markup from the given string.

    :param html: the HTML string to be cleaned
    :type html: str
    :rtype: str
    """

    # First we remove inline JavaScript/CSS:
    cleaned = re.sub(r"(?is)<(script|style).*?>.*?(</\1>)", "", html.strip())
    # Then we remove html comments. This has to be done before removing regular
    # tags since comments can contain '>' characters.
    cleaned = re.sub(r"(?s)<!--(.*?)-->[\n]?", "", cleaned)
    # Next we can remove the remaining tags:
    cleaned = re.sub(r"(?s)<.*?>", " ", cleaned)
    # Finally, we deal with whitespace
    cleaned = re.sub(r"&nbsp;", " ", cleaned)
    cleaned = re.sub(r"\n", " ", cleaned)
    cleaned = re.sub(r"\s\s+", " ", cleaned)

    return cleaned.strip()


async def fetch(url, session, timeout):
    async with async_timeout.timeout(timeout):
        try:
            async with session.get(url) as response:
                return await response.text()
        except CancelledError:
            print("Server timeout to {}".format(url))
            return ""


async def run(urls, timeout, headers):
    tasks = []
    async with aiohttp.ClientSession(headers=headers) as session:
        for url in urls:
            task = asyncio.ensure_future(fetch(url, session, timeout))
            tasks.append(task)

        responses = await asyncio.gather(*tasks)
        return responses


async def get_texts(urls, clean=True, timeout=1.5, headers=HEADERS):
    responses = await run(urls, timeout, headers)

    return [html.unescape(clean_html(r).lower()) for r in responses] if clean else responses
