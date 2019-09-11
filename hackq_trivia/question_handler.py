import asyncio
import logging
import re
from string import punctuation
from time import time
from typing import Match

from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk.tag.perceptron import PerceptronTagger
from nltk.tokenize import sent_tokenize

from hackq_trivia.config import config
from hackq_trivia.searcher import Searcher


class QuestionHandler:
    def __init__(self, headers):
        self.simplified_output = config.getboolean("LIVE", "SimplifiedOutput")

        self.searcher = Searcher(headers, asyncio.get_event_loop())

        self.STOPWORDS = set(stopwords.words("english")) - {"most", "least"}
        self.nltk_tagger = PerceptronTagger()

        self.SEARCH_METHODS_TO_USE = [self.__method1, self.__method2]

        self.logger = logging.getLogger(__name__)

    def answer_question(self, question, original_choices):
        self.logger.info("Searching...")
        start_time = time()

        question_lower = question.lower()

        reverse = "NOT" in question or "NEVER" in question or \
                  ("least" in question_lower and "at least" not in question_lower)

        choice_groups = [[choice.translate(str.maketrans({key: None for key in punctuation})),
                          choice.translate(str.maketrans({key: " " for key in punctuation}))]
                         for choice in original_choices]
        choices = sum(choice_groups, [])

        # Step 1: Search Google for results


        self.logger.info(f"Search took {round(time() - start_time, 2)} seconds")

    def __method1(self, texts, answers, answer_groups, reverse):
        """
        Returns the answer with the best number of exact occurrences in texts.
        :param texts: List of webpages (strings) to analyze
        :param answers: List of answers
        :param answer_groups: Groupings of different ways of writing the answer
        :param reverse: True if the best answer occurs the least, False otherwise
        :return: Answer that occurs the most/least in the texts, empty string if there is a tie
        """
        self.logger.info("Running method 1")

        counts = {answer: 0 for answer in answers}
        for text in texts:
            for answer in answers:
                counts[answer] += text.count(answer)

        self.logger.info(counts)
        return self.__get_best_answer(counts, answer_groups, reverse)

    def __method2(self, texts, answers, answer_groups, reverse):
        """
        Returns the answers with the best number of occurrences of the answer's keywords in texts.
        :param texts: List of webpages (strings) to analyze
        :param answers: List of answers
        :param answer_groups: Groupings of different ways of writing the answer
        :param reverse: True if the best answer occurs the least, False otherwise
        :return: Answer that occurs the most/least in the texts, empty string if there is a tie
        """
        self.logger.info("Running method 2")

        counts = {answer: 0 for answer in answers}
        for text in texts:
            for answer in answers:
                for keyword in self.find_keywords(answer):
                    counts[answer] += text.count(keyword.lower())

        self.logger.info(counts)
        return self.__get_best_answer(counts, answer_groups, reverse)

    def find_keywords(self, text: str):
        """
        Returns the keywords from a string containing text, in the order they appear.
        Keywords:
        - Words within quotes
        - Consecutively capitalized words
        - Words that aren't stopwords
        :param text: Text to analyze
        :return: List of keywords of text
        """
        keyword_indices = {}

        def process_match(match: Match[str]):
            keyword_indices[match[1]] = match.start()
            return " " * len(match[0])

        # Remove capitalization at start of sentences
        sentences = sent_tokenize(text)
        text = " ".join(sentence[0].lower() + sentence[1:] for sentence in sentences)

        # Remove all punctuation except quotes
        text = text.translate(str.maketrans({key: None for key in set(punctuation) - {"\"", "'"}}))

        # Find words in quotes and replace words in quotes with whitespace 
        # of same length to avoid matching words multiple times
        text = re.sub('"([^"]*)"', process_match, text)

        # Find and replace consecutively capitalized words (includes single
        # apostrophe to match possessives). Slightly modified from this accepted answer:
        # https://stackoverflow.com/a/9526027/6686559
        text = re.sub(r"([A-Z][a-z]+(?=\s[A-Z])(?:\s[A-Z][a-z']+)+)", process_match, text)

        # Find remaining words that are not stopwords
        for m in re.finditer(r"\S+", text):
            if m[0] not in self.STOPWORDS:
                keyword_indices[m[0]] = m.start()

        # Return keywords, sorted by index of occurrence
        keywords = list(sorted(keyword_indices, key=keyword_indices.get))
        return keywords

    def find_nouns(self, text, num_words, reverse=False):
        tokens = word_tokenize(text)
        tags = [tag for tag in self.nltk_tagger.tag(tokens) if tag[1] != "POS"]

        if not self.simplified_output:
            self.logger.info(tags)

        tags = tags[:num_words] if not reverse else tags[-num_words:]

        nouns = []
        consecutive_nouns = []

        for tag in tags:
            tag_type = tag[1]
            word = tag[0]

            if "NN" not in tag_type and len(consecutive_nouns) > 0:
                nouns.append(" ".join(consecutive_nouns))
                consecutive_nouns = []
            elif "NN" in tag_type:
                consecutive_nouns.append(word)

        if len(consecutive_nouns) > 0:
            nouns.append(" ".join(consecutive_nouns))

        return nouns

    @staticmethod
    def __get_best_answer(all_scores, choice_groups, reverse=False):
        # Add scores of the same answer together due to two ways of removing punctuation
        scores = {choices[0]: sum(all_scores[choice] for choice in choices) for choices in choice_groups}

        best_value = min(scores.values()) if reverse else max(scores.values())

        # Make sure the scores are not all 0 and the best value doesn't occur more than once
        if not all(c == 0 for c in scores.values()) and list(scores.values()).count(best_value) == 1:
            return min(scores, key=scores.get) if reverse else max(scores, key=scores.get)
        return ""