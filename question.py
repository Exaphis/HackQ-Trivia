import logging
from time import time

from tools import init_logger, punctuation_to_space, punctuation_to_none


class QuestionHandler:
    def __init__(self):
        if "HackQ" not in logging.Logger.manager.loggerDict:
            init_logger()
        self.logger = logging.getLogger("HackQ")

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

    def __method1(self):
        pass

    def __method2(self):
        pass

    def __method3(self):
        pass

    @staticmethod
    def get_best_answer(all_scores, choice_groups, reverse):
        # Add scores of the same answer together due to two ways of removing punctuation
        scores = {choices[0]: sum(all_scores[choice] for choice in choices) for choices in choice_groups}

        best_value = min(scores.values()) if reverse else max(scores.values())
        if not all(c == 0 for c in scores.values()) and list(scores.values()).count(best_value) == 1:
            return min(scores, key=scores.get) if reverse else max(scores, key=scores.get)
        return "None"
