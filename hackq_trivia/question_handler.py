import logging
import re
import string
from time import time
from typing import Dict, List, Match

import nltk
import colorama

from hackq_trivia.config import config
from hackq_trivia.searcher import Searcher


class QuestionHandler:
    def __init__(self):
        self.simplified_output = config.getboolean('LIVE', 'SimplifiedOutput')
        self.num_sites = config.getint('SEARCH', 'NumSitesToSearch')

        self.searcher = Searcher()
        self.search_methods_to_use = [self._method1, self._method2]
        self.logger = logging.getLogger(__name__)

        self.stopwords = set(nltk.corpus.stopwords.words('english')) - {'most', 'least'}
        self.punctuation_to_none = str.maketrans({key: None for key in string.punctuation})
        self.punctuation_to_space = str.maketrans({key: ' ' for key in string.punctuation})

    async def close(self):
        await self.searcher.close()

    async def answer_question(self, question: str, original_choices: List[str]):
        self.logger.info('Searching...')
        start_time = time()

        question_lower = question.lower()

        reverse = 'NOT' in question or 'NEVER' in question or 'NEITHER' in question or \
                  ('least' in question_lower and 'at least' not in question_lower)

        choice_groups = [[choice.translate(self.punctuation_to_none),
                          choice.translate(self.punctuation_to_space)]
                         for choice in original_choices]
        choices = sum(choice_groups, [])

        # Step 1: Search web for results
        keyword_start_time = time()
        question_keywords = self.find_keywords(question)
        if not self.simplified_output:
            self.logger.info(f'Question keywords: {question_keywords}')
        self.logger.debug(f'Keywords took {round(time() - keyword_start_time, 2)} seconds')

        search_start_time = time()
        links = await self.searcher.get_search_links(' '.join(question_keywords), self.num_sites)
        self.logger.debug(f'Web search took {round(time() - search_start_time, 2)} seconds')
        self.logger.debug(f'Found links: {links}')

        # Step 2: Fetch links and clean up text
        fetch_start_time = time()
        link_texts = [Searcher.html_to_visible_text(html).translate(self.punctuation_to_none)
                      for html in await self.searcher.fetch_multiple(links)]
        self.logger.debug(f'Fetching took {round(time() - fetch_start_time, 2)} seconds')

        # Step 3: Find best answer for all search methods
        post_process_start_time = time()
        answers = []
        for search_method in self.search_methods_to_use:
            answer = await search_method(link_texts, choices, choice_groups, reverse)
            answers.append(answer)
            if answer:
                self.logger.info(answer, extra={'pre': colorama.Fore.BLUE})
            else:
                self.logger.info('Tie', extra={'pre': colorama.Fore.BLUE})

        self.logger.debug(f'Post-processing took {round(time() - post_process_start_time, 2)} seconds')

        self.logger.info(f'Search took {round(time() - start_time, 2)} seconds')
        return answers

    async def _method1(self, texts: List[str], answers: List[str],
                       answer_groups: List[List[str]], reverse: bool) -> str:
        """
        Returns the answer with the best number of exact occurrences in texts.
        :param texts: List of webpages (strings) to analyze
        :param answers: List of answers
        :param answer_groups: Groupings of different ways of writing the answer
        :param reverse: True if the best answer occurs the least, False otherwise
        :return: Answer that occurs the most/least in the texts, empty string if there is a tie
        """
        self.logger.info('Running method 1')

        counts = {answer: 0 for answer in answers}
        for text in texts:
            for answer in answers:
                counts[answer] += text.count(f' {answer.lower()} ')

        self.logger.info(counts)
        return self.__get_best_answer(counts, answer_groups, reverse)

    async def _method2(self, texts: List[str], answers: List[str],
                       answer_groups: List[List[str]], reverse: bool) -> str:
        """
        Returns the answers with the best number of occurrences of the answer's keywords in texts.
        :param texts: List of webpages (strings) to analyze
        :param answers: List of answers
        :param answer_groups: Groupings of different ways of writing the answer
        :param reverse: True if the best answer occurs the least, False otherwise
        :return: Answer that occurs the most/least in the texts, empty string if there is a tie
        """
        self.logger.info('Running method 2')

        counts = {answer: 0 for answer in answers}
        for text in texts:
            for answer in answers:
                for keyword in self.find_keywords(answer, sentences=False):
                    counts[answer] += text.count(f' {keyword.lower()} ')

        self.logger.info(counts)
        return self.__get_best_answer(counts, answer_groups, reverse)

    def find_keywords(self, text: str, sentences: bool = True) -> List[str]:
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
        text = text.translate(str.maketrans({key: None for key in set(string.punctuation) - {'"', "'"}}))

        # If a match is encountered:
        #   Add entry to keyword_indices
        #   Return string containing spaces of same length as the match to replace match with
        def process_match(match: Match[str]):
            keyword_indices[match[1]] = match.start()
            return ' ' * len(match[0])

        # Find words in quotes and replace words in quotes with whitespace 
        # of same length to avoid matching words multiple times
        text = re.sub('"([^"]*)"', process_match, text)

        # Find and replace consecutively capitalized words (includes single
        # apostrophe to match possessives). Slightly modified from this accepted answer:
        # https://stackoverflow.com/a/9526027/6686559
        text = re.sub(r"([A-Z][a-z]+(?=\s[A-Z])(?:\s[A-Z][a-z']+)+)", process_match, text)

        # Find remaining words that are not stopwords
        for m in re.finditer(r'\S+', text):
            if m[0] not in self.stopwords:
                keyword_indices[m[0]] = m.start()

        # Return keywords, sorted by index of occurrence
        keywords = list(sorted(keyword_indices, key=keyword_indices.get))
        # TODO: handle plural and singular, see test_question_handler.py
        return keywords

    @staticmethod
    def __get_best_answer(all_scores: Dict, choice_groups: List[List[str]], reverse: bool = False):
        """
        Returns best answer based on scores for each choice and groups of choices.
        :param all_scores: Dict mapping choices to scores
        :param choice_groups: List of lists (groups) of choices
        :param reverse: If True, return lowest scoring choice group, otherwise return highest
        :return: String (first entry in group) of the group with the highest/lowest total score
        """
        # Add scores of the same answer together due to two ways of removing punctuation
        scores = {choices[0]: sum(all_scores[choice] for choice in choices) for choices in choice_groups}

        best_value = min(scores.values()) if reverse else max(scores.values())

        # Make sure the scores are not all 0 and the best value doesn't occur more than once
        if not all(c == 0 for c in scores.values()) and list(scores.values()).count(best_value) == 1:
            return min(scores, key=scores.get) if reverse else max(scores, key=scores.get)
        return ''
