import itertools
import re
import time
from collections import defaultdict

from colorama import Fore, Style

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

    question_lower = question.lower()

    reverse = "NOT" in question or\
              ("least" in question_lower and "at least" not in question_lower) or\
              "NEVER" in question

    quoted = re.findall('"([^"]*)"', question_lower)  # Get all words in quotes
    no_quote = question_lower
    for quote in quoted:
        no_quote = no_quote.replace(f"\"{quote}\"", "1placeholder1")

    question_keywords = search.find_keywords(no_quote)
    for quote in quoted:
        question_keywords[question_keywords.index("1placeholder1")] = quote

    print(question_keywords)
    search_results = await search.search_google("+".join(question_keywords), 5)
    print(search_results)

    search_text = [x.translate(punctuation_to_none) for x in await search.get_clean_texts(search_results)]

    best_answer = await __search_method1(search_text, answers, reverse)
    if best_answer == "":
        best_answer = await __search_method2(search_text, answers, reverse)

    if best_answer != "":
        print(f"{Fore.GREEN}{best_answer}{Style.RESET_ALL}\n")

    # Get key nouns for Method 3
    key_nouns = set(quoted)

    q_word_location = search.find_q_word_location(question_lower)
    if len(key_nouns) == 0:
        if q_word_location > len(question) // 2 or q_word_location == -1:
            key_nouns.update(search.find_nouns(question, num_words=5))
        else:
            key_nouns.update(search.find_nouns(question, num_words=5, reverse=True))

        key_nouns -= {"type"}

    # Add consecutive capitalised words (Thanks talentoscope!)
    key_nouns.update(re.findall("([A-Z][a-z]+(?=\s[A-Z])(?:\s[A-Z][a-z]+)+)",
                                " ".join([w for idx, w in enumerate(question.split(" ")) if idx != q_word_location])))

    key_nouns = {noun.lower() for noun in key_nouns}
    print(f"Question nouns: {key_nouns}")
    answer3 = await __search_method3(list(set(question_keywords)), key_nouns, original_answers, reverse)
    print(f"{Fore.GREEN}{answer3}{Style.RESET_ALL}")

    print(f"Search took {time.time() - start} seconds")


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
            counts[answer] += len(re.findall(f" {answer} ", text))

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
                keyword_counts[keyword] += len(re.findall(f" {keyword} ", text))

    print(counts)
    counts_sum = {answer: sum(keyword_counts.values()) for answer, keyword_counts in counts.items()}

    if not all(c == 0 for c in counts_sum.values()):
        return min(counts_sum, key=counts_sum.get) if reverse else max(counts_sum, key=counts_sum.get)
    return ""


async def __search_method3(question_keywords, question_key_nouns, answers, reverse):
    """
    Returns the answer with the maximum number of occurrences of the question keywords in its searches.
    :param question_keywords: Keywords of the question
    :param question_key_nouns: Key nouns of the question
    :param answers: List of answers
    :param reverse: True if the best answer occurs the least, False otherwise
    :return: Answer whose search results contain the most keywords of the question
    """
    print("Running method 3")
    search_results = await search.multiple_search(answers, 5)
    print("Search processed")
    answer_lengths = list(map(len, search_results))
    search_results = itertools.chain.from_iterable(search_results)

    texts = [x.translate(punctuation_to_none) for x in await search.get_clean_texts(search_results)]
    print("URLs fetched")
    answer_text_map = {}
    for idx, length in enumerate(answer_lengths):
        answer_text_map[answers[idx]] = texts[0:length]
        del texts[0:length]

    keyword_scores = {answer: 0 for answer in answers}
    noun_scores = {answer: 0 for answer in answers}

    # Create a dictionary of word to type of score so we avoid searching for the same thing twice in the same page
    word_score_map = defaultdict(list)
    for word in question_keywords:
        word_score_map[word].append("KW")
    for word in question_key_nouns:
        word_score_map[word].append("KN")

    answer_noun_scores_map = {}
    for answer, texts in answer_text_map.items():
        keyword_score = 0
        noun_score = 0
        noun_score_map = defaultdict(int)

        for text in texts:
            for keyword, score_types in word_score_map.items():
                score = len(re.findall(f" {keyword} ", text))
                if "KW" in score_types:
                    keyword_score += score
                if "KN" in score_types:
                    noun_score += score
                    noun_score_map[keyword] += score

        keyword_scores[answer] = keyword_score
        noun_scores[answer] = noun_score
        answer_noun_scores_map[answer] = noun_score_map

    print()
    print("\n".join([f"{answer}: {dict(scores)}" for answer, scores in answer_noun_scores_map.items()]))
    print()

    print(f"Keyword scores: {keyword_scores}")
    print(f"Noun scores: {noun_scores}")
    if set(noun_scores.values()) != {0}:
        return min(noun_scores, key=noun_scores.get) if reverse else max(noun_scores, key=noun_scores.get)
    if set(keyword_scores.values()) != {0}:
        return min(keyword_scores, key=keyword_scores.get) if reverse else max(keyword_scores, key=keyword_scores.get)
    return ""
