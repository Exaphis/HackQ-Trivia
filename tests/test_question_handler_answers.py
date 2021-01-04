import asyncio

from hackq_trivia.question_handler import QuestionHandler
from hackq_trivia.hq_main import init_root_logger


async def test():
    qh = QuestionHandler()
    # fails because all pages say foot/footwear instead of feet
    # await qh.answer_question('In the 19th century, where were spats typically worn?',
    #                          ['Ears', 'Arms', 'Feet'])

    # await qh.answer_question('Which of these games is played on a court?',
    #                          ['Basketball', 'Super Mario Kart', 'Uno'])

    # for is removed as a stopword
    await qh.answer_question("What do NEITHER of the N's in CNN stand for?",
                             ['News', 'Netflix', 'Network'])
    await qh.close()

if __name__ == '__main__':
    init_root_logger()

    asyncio.run(test())
