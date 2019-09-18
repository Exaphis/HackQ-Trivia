import logging
import re
import string
from time import time
from typing import Match

import nltk
import colorama

from hackq_trivia.config import config
from hackq_trivia.searcher import Searcher


class QuestionHandler:
    STOPWORDS = set(nltk.corpus.stopwords.words("english")) - {"most", "least"}
    PUNCTUATION_TO_NONE = str.maketrans({key: None for key in string.punctuation})
    PUNCTUATION_TO_SPACE = str.maketrans({key: " " for key in string.punctuation})

    def __init__(self):
        self.simplified_output = config.getboolean("LIVE", "SimplifiedOutput")
        self.searcher = Searcher()
        self.perceptron_tagger = nltk.tag.perceptron.PerceptronTagger()
        self.search_methods_to_use = [self.__method1, self.__method2]
        self.logger = logging.getLogger(__name__)

    async def close(self):
        await self.searcher.close()

    async def answer_question(self, question, original_choices):
        self.logger.info("Searching...")
        start_time = time()

        question_lower = question.lower()

        reverse = "NOT" in question or "NEVER" in question or \
                  ("least" in question_lower and "at least" not in question_lower)

        choice_groups = [[choice.translate(QuestionHandler.PUNCTUATION_TO_NONE),
                          choice.translate(QuestionHandler.PUNCTUATION_TO_SPACE)]
                         for choice in original_choices]
        choices = sum(choice_groups, [])

        # Step 1: Search Google for results
        question_keywords = self.find_keywords(question)
        if not self.simplified_output:
            self.logger.info(f"Question keywords: {question_keywords}")

        links = self.searcher.get_google_links(" ".join(question_keywords), 5)

        # Step 2: Fetch links and clean up text
        link_texts = [Searcher.html_to_visible_text(html).translate(QuestionHandler.PUNCTUATION_TO_NONE)
                      for html in await self.searcher.fetch_multiple(links)]

        # Step 3: Find best answer for all search methods
        for search_method in self.search_methods_to_use:
            self.logger.info(search_method(link_texts, choices, choice_groups, reverse),
                             extra={"pre": colorama.Fore.BLUE})

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
                counts[answer] += text.count(" " + answer.lower() + " ")

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
                for keyword in self.find_keywords(answer, sentences=False):
                    counts[answer] += text.count(" " + keyword.lower() + " ")

        self.logger.info(counts)
        return self.__get_best_answer(counts, answer_groups, reverse)

    def find_keywords(self, text: str, sentences=True):
        """
        Returns the keywords from a string containing text, in the order they appear.
        Keywords:
        - Words within quotes
        - Consecutively capitalized words
        - Words that aren't stopwords
        :param text: Text to analyze
        :param sentences: Whether or not text is comprised of sentences
        :return: List of keywords of text
        """
        keyword_indices = {}

        if sentences:
            # Remove capitalization at start of sentences
            sentences = nltk.tokenize.sent_tokenize(text)
            text = " ".join(sentence[0].lower() + sentence[1:] for sentence in sentences)

        # Remove all punctuation except quotes
        text = text.translate(str.maketrans({key: None for key in set(string.punctuation) - {"\"", "'"}}))

        # If a match is encountered:
        #   Add entry to keyword_indices
        #   Return string containing spaces of same length as the match to replace match with
        def process_match(match: Match[str]):
            keyword_indices[match[1]] = match.start()
            return " " * len(match[0])

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
        # TODO: handle plural and singular
        return keywords

    def find_nouns(self, text, num_words, reverse=False):
        tokens = nltk.word_tokenize(text)
        tags = [tag for tag in self.perceptron_tagger.tag(tokens) if tag[1] != "POS"]

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
