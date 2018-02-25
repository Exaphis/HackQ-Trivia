import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from time import sleep

import websockets

import question
import search


async def websocket_handler(uri, socket_headers):
    try:
        async with websockets.connect(uri, extra_headers=socket_headers) as websocket:
            async for message in websocket:
                # Remove control characters in the WebSocket message
                message = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", message)
                message_data = json.loads(message)
                logging.info(message_data)

                if message_data["type"] == "question" and "answers" in message_data:
                    question_s = message_data["question"]
                    answers = [ans["text"] for ans in message_data["answers"] if ans["text"].strip() != ""]
                    print("\n" * 5)
                    print("Question detected.")
                    print(question_s)
                    print(answers)
                    print()
                    print(await question.answer_question(question_s, answers))
                elif message_data["type"] == "broadcastEnded" and "reason" not in message_data:
                    print("Broadcast ended.")
    except websockets.ConnectionClosed:
        pass
    print("Socket closed.")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(filename="data.log", level=logging.INFO, filemode="w")

    # Read in bearer token and user ID
    with open("conn_settings.txt", "r") as conn_settings:
        BEARER_TOKEN = conn_settings.readline().strip().split("=")[1]
        USER_ID = conn_settings.readline().strip().split("=")[1]

    print("getting")
    main_url = "https://api-quiz.hype.space/shows/now?type=hq&userId={}".format(USER_ID)
    headers = {"x-hq-client": "Android/1.1.3",
               "Authorization": "Bearer " + BEARER_TOKEN,
               "x-hq-stk": "MQ==",
               "Host": "api-quiz.hype.space",
               "Connection": "Keep-Alive",
               "Accept-Encoding": "gzip",
               "User-Agent": "okhttp/3.8.0"}

    while True:
        print()
        response = asyncio.get_event_loop().run_until_complete(
            search.get_texts([main_url], clean=False, timeout=1.5, headers=headers))[0]

        # Strip control characters in the API response
        response_text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", response)
        try:
            response_data = json.loads(response_text)
        except json.decoder.JSONDecodeError:
            print("Server response not JSON, retrying in 30 seconds.")
            sleep(30)
            continue

        logging.info(response_data)

        if "broadcast" not in response_data or response_data["broadcast"] is None:
            print("Show not on.")
            next_time = datetime.strptime(response_data["nextShowTime"], "%Y-%m-%dT%H:%M:%S.000Z")
            print("Next show time: {}".format((next_time - timedelta(hours=5)).strftime("%Y-%m-%d %I:%M %p")))
            print("Prize: " + response_data["nextShowPrize"])
            sleep(1)
        else:
            socket = response_data["broadcast"]["socketUrl"].replace("https", "wss")
            print("Show active, connecting to socket at {}".format(socket))
            asyncio.get_event_loop().run_until_complete(websocket_handler(socket, headers))
