import re
import time
from multiprocessing import cpu_count

from joblib import Parallel, delayed

import search

punctuation_to_none = str.maketrans({key: None for key in "!\"#$%&\'()*+,-.:;<=>?@[\\]^_`{|}~"})


def get_no_punctuation_text(url):
    return search.get_text(url).translate(punctuation_to_none)


def answer_question(question, answers):
    print("Searching")
    start = time.time()

    answers = list(map(lambda x: x.translate(punctuation_to_none), answers))

    reverse = "NOT" in question or ("least" in question.lower() and "at least" not in question.lower())
    question_keywords = search.find_keywords(question)
    print(question_keywords)
    search_results = search.search_google(" ".join(question_keywords), 5)
    print(search_results)

    # Parallelize access of found URLs
    search_text = Parallel(n_jobs=cpu_count())(
        delayed(get_no_punctuation_text)(url) for url in search_results)

    best_answer = __search_method1(search_text, answers, reverse)
    best_answer = best_answer if best_answer != "" else __search_method2(search_text, answers, reverse)
    print("Search took {} seconds".format(time.time() - start))
    return best_answer


def __search_method1(texts, answers, reverse):
    """
    Returns the answer with the maximum/minimum number of exact occurrences in the texts.
    :param texts: List of text to analyze
    :param answers: List of answers
    :param reverse: True if the best answer occurs the least, False otherwise
    :return: Answer that occurs the most/least in the texts, empty string if there is a tie
    """

    counts = {answer.lower(): 0 for answer in answers}

    for text in texts:
        for answer in counts:
            counts[answer] += len(re.findall(" {} ".format(answer), text))

    print(counts)

    # If not all answers have count of 0 and the best value doesn't occur more than once, return the best answer
    best_value = min(counts.values()) if reverse else max(counts.values())
    if not all(c == 0 for c in counts.values()) and list(counts.values()).count(best_value) == 1:
        return min(counts, key=counts.get) if reverse else max(counts, key=counts.get)
    else:
        return ""


def __search_method2(texts, answers, reverse):
    """
    Return the answer with the maximum/minimum number of keyword occurrences in the texts.
    :param texts: List of text to analyze
    :param answers: List of answers
    :param reverse: True if the best answer occurs the least, False otherwise
    :return: Answer whose keywords occur most/least in the texts
    """

    counts = {answer: {keyword: 0 for keyword in search.find_keywords(answer)} for answer in answers}

    for text in texts:
        for keyword_counts in counts.values():
            for keyword in keyword_counts:
                keyword_counts[keyword] += len(re.findall(" {} ".format(keyword), text))

    print(counts)
    counts_sum = {answer: sum(keyword_counts.values()) for answer, keyword_counts in counts.items()}
    return min(counts_sum, key=counts_sum.get) if reverse else max(counts_sum, key=counts_sum.get)


