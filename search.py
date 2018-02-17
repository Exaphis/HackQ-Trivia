import re

import requests
from bs4 import BeautifulSoup
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer

STOP = set(stopwords.words("english"))
tokenizer = RegexpTokenizer(r"\w+")
HEADER = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:58.0) Gecko/20100101 Firefox/58.0",
          "Accept": "*/*",
          "Accept-Language": "en-US,en;q=0.5",
          "Accept-Encoding": "gzip, deflate"}


def find_keywords(words):
    """
    Returns the list of words given without stopwords.
    :param words: List of words
    :return: Words without stopwords
    """
    return list(filter(lambda w: w not in STOP, tokenizer.tokenize(words.lower())))


def search_google(question, num_results):
    """
    Returns num_results urls from a google search of question.
    :param question: Question to search
    :param num_results: Number of results to return
    :return: List of length num_results of urls retrieved from the search
    """
    # Could use Google's Custom Search API here, limit of 100 queries per day
    # result = service.cse().list(q=question, cx=CSE_ID, num=num_results).execute()
    # return result["items"]

    page = requests.get("https://www.google.com/search?q={}&ie=utf-8&oe=utf-8&client=firefox-b-1-ab"
                        .format(question))
    soup = BeautifulSoup(page.content, "html.parser")
    results = list(map(str, soup.findAll("h3", {"class": "r"})))
    links = [r[30:r.index("&amp;sa=U")] for r in results if "/url?q=" in r and "class=\"sla\"" not in r]
    return links[:num_results]


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


def get_text(url):
    """
    Returns the text in a web page. Returns an empty string if timeout is reached.
    :param url: URL to get text from
    :return: Text of the web page, "" if timeout reached
    """
    try:
        page_text = requests.get(url, timeout=1.5).text
        return clean_html(page_text).lower()
    except:
        print("Connection error/timeout to " + url)
        return ""
