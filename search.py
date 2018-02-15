import re
from urllib.error import HTTPError

import requests
from googlesearch import search
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
from requests.exceptions import Timeout

STOP = set(stopwords.words("english"))
tokenizer = RegexpTokenizer(r"\w+")


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

    try:
        results = search(question, num=num_results)
        return [next(results) for _ in range(num_results)]
    except HTTPError as http_err:
        print(http_err.headers)  # Dump the headers to see if there's more information
        print(http_err.read())
        exit()


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
    except Timeout:
        return ""
