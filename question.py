import re
import time

import search

punctuation_to_none = str.maketrans({key: None for key in "!\"#$%&\'()*+,-.:;<=>?@[\\]^_`{|}~"})


def answer_question(question, answers):
    print("Searching")
    start = time.time()

    answers = list(map(lambda x: x.translate(punctuation_to_none), answers))

    reverse = "NOT" in question or "least" in question.lower()
    question_keywords = search.find_keywords(question)
    print(question_keywords)
    search_results = search.search_google(" ".join(question_keywords), 3)
    print(search_results)
    search_text = []

    for url in search_results:
        text = search.get_text(url).translate(punctuation_to_none)
        print(text)
        search_text.append(text)

    best_answer = search_method1(search_text, answers, reverse)
    best_answer = best_answer if best_answer != "" else search_method2(search_text, answers, reverse)
    print("Search took {} seconds".format(time.time() - start))
    return best_answer


def search_method1(texts, answers, reverse):
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


def search_method2(texts, answers, reverse):
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


def search_method3(answers, question_keywords, reverse):
    """
    Returns the answer whose search results appear most often
    :param answers:
    :param question_keywords:
    :param reverse:
    :return:
    """

