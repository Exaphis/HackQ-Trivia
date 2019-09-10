import logging
from time import time

from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk.tag.perceptron import PerceptronTagger
from nltk.tokenize import RegexpTokenizer

from hackq_trivia.config import config
from hackq_trivia.tools import punctuation_to_space, punctuation_to_none


class QuestionHandler:
    def __init__(self, headers):
        self.simplified_output = config.getboolean("LIVE", "SimplifiedOutput")

        self.STOPWORDS = set(stopwords.words("english")) - {"most", "least"}
        self.nltk_tokenizer = RegexpTokenizer(r"\w+")
        self.nltk_tagger = PerceptronTagger()

        self.logger = logging.getLogger(__name__)

    def answer_question(self, question, original_choices):
        print("Searching...")
        start_time = time()

        question_lower = question.lower()

        reverse = "NOT" in question or "NEVER" in question or \
                  ("least" in question_lower and "at least" not in question_lower)

        choice_groups = [[choice.translate(punctuation_to_none),
                          choice.translate(punctuation_to_space)] for choice in original_choices]
        choices = sum(choice_groups, [])

        print(f"Search took {round(time() - start_time, 2)} seconds")

    def __method1(self, texts, answers, answer_groups, reverse):
        """
        Returns the answer with the best number of exact occurrences in texts.
        :param texts: List of webpages (strings) to analyze
        :param answers: List of answers
        :param answer_groups: Groupings of different ways of writing the answer
        :param reverse: True if the best answer occurs the least, False otherwise
        :return: Answer that occurs the most/least in the texts, empty string if there is a tie
        """
        print("Running method 1")

        counts = {answer: 0 for answer in answers}
        for text in texts:
            for answer in answers:
                counts[answer] += text.count(answer)

        print(counts)
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
        print("Running method 2")

        counts = {answer: 0 for answer in answers}
        for text in texts:
            for answer in answers:
                for keyword in self.find_keywords(answer):
                    counts[answer] += text.count(keyword.lower())

        print(counts)
        return self.__get_best_answer(counts, answer_groups, reverse)

    def find_keywords(self, words: str):
        return [w for w in self.nltk_tokenizer.tokenize(words.lower()) if w not in self.STOPWORDS]

    def find_nouns(self, text, num_words, reverse=False):
        tokens = word_tokenize(text)
        tags = [tag for tag in self.nltk_tagger.tag(tokens) if tag[1] != "POS"]

        if not self.simplified_output:
            print(tags)

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
