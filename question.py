import ahocorasick
import logging
from time import time

from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk.tag.perceptron import PerceptronTagger
from nltk.tokenize import RegexpTokenizer

from settings import config
from tools import init_logger, punctuation_to_space, punctuation_to_none


class QuestionHandler:
    def __init__(self):
        if "HackQ" not in logging.Logger.manager.loggerDict:
            init_logger()
        self.logger = logging.getLogger("HackQ")

        self.simplified_output = config.getboolean("LIVE", "SimplifiedOutput")

        self.fsa = ahocorasick.Automaton()

        self.STOPWORDS = set(stopwords.words("english")) - {"most", "least"}
        self.nltk_tokenizer = RegexpTokenizer(r"\w+")
        self.nltk_tagger = PerceptronTagger()

    def answer_question(self, question, original_choices):
        print("Searching...")
        start_time = time()

        question_lower = question.lower()

        reverse = "NOT" in question or \
                  ("least" in question_lower and "at least" not in question_lower) or \
                  "NEVER" in question

        choice_groups = [list({choice.translate(punctuation_to_none),
                               choice.translate(punctuation_to_space)}) for choice in original_choices]
        choices = sum(choice_groups, [])

        print(f"Search took {round(time()-start_time, 2)} seconds")

    def __method1(self, texts, answers, reverse):
        print("Running method 1")

        counts = {}
        for idx, a in enumerate(answers):
            answer = a.lower()
            counts[answer] = 0
            self.fsa.add_word(f" {answer} ", idx)

        self.fsa.make_automaton()

        for text in texts:
            for _, (_, match) in self.fsa.iter(text):
                counts[match] += 1
        self.fsa.clear()

        print(counts)
        # If not all answers have count of 0 and the best value doesn't occur more than once, return the best answer
        best_value = min(counts.values()) if reverse else max(counts.values())
        if not all(c == 0 for c in counts.values()) and list(counts.values()).count(best_value) == 1:
            print(counts)
            return min(counts, key=counts.get) if reverse else max(counts, key=counts.get)

        return ""

    def __method2(self):
        print("Running method 2")

    def __method3(self):
        pass

    def find_keywords(self, words):
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
    def get_best_answer(all_scores, choice_groups, reverse=False):
        # Add scores of the same answer together due to two ways of removing punctuation
        scores = {choices[0]: sum(all_scores[choice] for choice in choices) for choices in choice_groups}

        best_value = min(scores.values()) if reverse else max(scores.values())
        if not all(c == 0 for c in scores.values()) and list(scores.values()).count(best_value) == 1:
            return min(scores, key=scores.get) if reverse else max(scores, key=scores.get)
        return "None"
