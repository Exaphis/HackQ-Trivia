import asyncio

from hackq_trivia.question_handler import QuestionHandler
from hackq_trivia.hq_main import HackQ


async def test():
    qh = QuestionHandler()
    # await qh.answer_question("Which of these shows just announced three new cast members?",
    #                          ["Saturday Night Live", "M*A*S*H", "Supernatural"])
    await qh.answer_question("In the 19th century, where were spats typically worn?",
                             ["Ears", "Arms", "Feet"])
    await qh.close()

if __name__ == "__main__":
    HackQ.init_root_logger()

    asyncio.run(test())
