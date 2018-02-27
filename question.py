import itertools
import re
import time

import search

punctuation_to_none = str.maketrans({key: None for key in "!\"#$%&\'()*+,-.:;<=>?@[\\]^_`{|}~�"})
punctuation_to_space = str.maketrans({key: " " for key in "!\"#$%&\'()*+,-.:;<=>?@[\\]^_`{|}~�"})


async def answer_question(question, original_answers):
    print("Searching")
    start = time.time()

    answers = []
    for ans in original_answers:
        answers.append(ans.translate(punctuation_to_none))
        answers.append(ans.translate(punctuation_to_space))
    answers = list(dict.fromkeys(answers))
    print(answers)

    reverse = "NOT" in question or ("least" in question.lower() and "at least" not in question.lower())
    question_keywords = search.find_keywords(question)
    print(question_keywords)
    search_results = await search.search_google("+".join(question_keywords), 5)
    print(search_results)

    search_text = [x.translate(punctuation_to_none) for x in await search.get_clean_texts(search_results)]

    best_answer = await __search_method1(search_text, answers, reverse)
    if best_answer == "":
        best_answer = await __search_method2(search_text, answers, reverse)
    print(best_answer + "\n")

    answer3 = await __search_method3(question_keywords, original_answers, reverse)
    print(answer3)

    print("Search took {} seconds".format(time.time() - start))
    return ""


async def __search_method1(texts, answers, reverse):
    """
    Returns the answer with the maximum/minimum number of exact occurrences in the texts.
    :param texts: List of text to analyze
    :param answers: List of answers
    :param reverse: True if the best answer occurs the least, False otherwise
    :return: Answer that occurs the most/least in the texts, empty string if there is a tie
    """
    print("Running method 1")
    counts = {answer.lower(): 0 for answer in answers}

    for text in texts:
        for answer in counts:
            counts[answer] += len(re.findall(" {} ".format(answer), text))

    print(counts)

    # If not all answers have count of 0 and the best value doesn't occur more than once, return the best answer
    best_value = min(counts.values()) if reverse else max(counts.values())
    if not all(c == 0 for c in counts.values()) and list(counts.values()).count(best_value) == 1:
        return min(counts, key=counts.get) if reverse else max(counts, key=counts.get)
    return ""


async def __search_method2(texts, answers, reverse):
    """
    Return the answer with the maximum/minimum number of keyword occurrences in the texts.
    :param texts: List of text to analyze
    :param answers: List of answers
    :param reverse: True if the best answer occurs the least, False otherwise
    :return: Answer whose keywords occur most/least in the texts
    """
    print("Running method 2")
    counts = {answer: {keyword: 0 for keyword in search.find_keywords(answer)} for answer in answers}

    for text in texts:
        for keyword_counts in counts.values():
            for keyword in keyword_counts:
                keyword_counts[keyword] += len(re.findall(" {} ".format(keyword), text))

    print(counts)
    counts_sum = {answer: sum(keyword_counts.values()) for answer, keyword_counts in counts.items()}

    if not all(c == 0 for c in counts_sum.values()):
        return min(counts_sum, key=counts_sum.get) if reverse else max(counts_sum, key=counts_sum.get)
    return ""


async def __search_method3(question_keywords, answers, reverse):
    """
    Returns the answer with the maximum number of occurrences of the question keywords in its searches.
    :param question_keywords: Keywords of the question
    :param answers: List of answers
    :param reverse: True if the best answer occurs the least, False otherwise
    :return: Answer whose search results contain the most keywords of the question
    """
    print("Running method 3")
    search_results = await search.multiple_search(answers, 3)
    print("Search processed")
    answer_lengths = list(map(len, search_results))
    search_results = itertools.chain.from_iterable(search_results)

    texts = [x.translate(punctuation_to_none) for x in await search.get_clean_texts(search_results)]
    print("URLs fetched")
    answer_text_map = {}
    for idx, length in enumerate(answer_lengths):
        answer_text_map[answers[idx]] = texts[0:length]
        del texts[0:length]

    # print(answer_text_map)
    scores = {answer: 0 for answer in answers}

    for answer, texts in answer_text_map.items():
        score = 0
        for text in texts:
            for keyword in question_keywords:
                score += len(re.findall(" {} ".format(keyword), text))
        scores[answer] = score

    print(scores)
    return min(scores, key=scores.get) if reverse else max(scores, key=scores.get)
