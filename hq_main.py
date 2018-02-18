import json
import logging
import re
from datetime import datetime, timedelta
from time import sleep

import requests
import websocket

import question


def on_message(ws, message):
    # Remove control characters in the WebSocket message
    message = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", message)
    message_data = json.loads(message)
    logging.info(str(message_data))

    if message_data["type"] == "question" and "answers" in message_data:
        question_s = message_data["question"]
        answers = list(map(lambda x: x["text"], message_data["answers"]))

        print("\n" * 5)
        print("Question detected.")
        print(question_s)
        print(answers)
        # print(message_data)
        print()
        print(question.answer_question(question_s, answers))
    elif message_data["type"] == "broadcastEnded" and "reason" not in message_data:
        print("Broadcast ended.")


def on_error(ws, error):
    print(error)


def on_close(ws):
    print("Socket closed.")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(filename="data.log", level=logging.INFO, filemode="w")

    # Read in bearer token and user ID
    with open("conn_settings.txt", "r") as conn_settings:
        BEARER_TOKEN = conn_settings.readline().strip().split("=")[1]
        USER_ID = conn_settings.readline().strip().split("=")[1]

    print("getting")

    headers = {"x-hq-client": "Android/1.1.3",
               "Authorization": "Bearer " + BEARER_TOKEN,
               "x-hq-stk": "MQ==",
               "Host": "api-quiz.hype.space",
               "Connection": "Keep-Alive",
               "Accept-Encoding": "gzip",
               "User-Agent": "okhttp/3.8.0"}
    hq_socket = None

    while True:
        print("")
        response = requests.get("https://api-quiz.hype.space/shows/now?type=hq&userId=" + USER_ID, headers=headers)
        # Strip control characters in the API response
        response_text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", response.text)
        try:
            response_data = json.loads(response_text)
        except json.decoder.JSONDecodeError:
            print("Server response not JSON, retrying in 30 seconds.")
            sleep(30)
            continue

        logging.info("{} {}".format(datetime.now(), response_data))
        # print(response_data)

        if "broadcast" not in response_data or response_data["broadcast"] is None:
            print("Show not on.")
            next_time = datetime.strptime(response_data["nextShowTime"], "%Y-%m-%dT%H:%M:%S.000Z")
            print("Next show time: {}".format((next_time - timedelta(hours=5)).strftime("%Y-%m-%d %I:%M %p")))
            print("Prize: " + response_data["nextShowPrize"])
            sleep(1)
        elif hq_socket is None:
            # print("Show active, connecting to socket.")
            hq_socket_url = response_data["broadcast"]["socketUrl"].replace("https", "wss")

            hq_socket = websocket.WebSocketApp(hq_socket_url,
                                               on_message=on_message,
                                               on_error=on_error,
                                               on_close=on_close,
                                               header=headers)
            hq_socket.run_forever()
            hq_socket = None
