import asyncio
import logging
import os
import time
from datetime import datetime

import colorama

import networking

# Set up color-coding
colorama.init()
# Set up logging
logging.basicConfig(filename="data.log", level=logging.INFO, filemode="w")

# Read in bearer token and user ID
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "conn_settings.txt"), "r") as conn_settings:
    settings = conn_settings.read().splitlines()
    settings = [line for line in settings if line != "" and line != " "]

    try:
        BEARER_TOKEN = settings[0].split("=")[1]
    except IndexError as e:
        logging.fatal(f"Settings read error: {settings}")
        raise e

print("getting")
main_url = f"https://api-quiz.hype.space/shows/now?type="
headers = {"Authorization": f"Bearer {BEARER_TOKEN}",
           "x-hq-client": "Android/1.3.0"}
# "x-hq-stk": "MQ==",
# "Connection": "Keep-Alive",
# "User-Agent": "okhttp/3.8.0"}

while True:
    print()
    try:
        response_data = asyncio.get_event_loop().run_until_complete(
            networking.get_json_response(main_url, timeout=1.5, headers=headers))
    except:
        print("Server response not JSON, retrying...")
        time.sleep(1)
        continue

    logging.info(response_data)

    if "broadcast" not in response_data or response_data["broadcast"] is None:
        if "error" in response_data and response_data["error"] == "Auth not valid":
            raise RuntimeError("Connection settings invalid")
        else:
            print("Show not on.")
            next_time = datetime.strptime(response_data["nextShowTime"], "%Y-%m-%dT%H:%M:%S.000Z")
            now = time.time()
            offset = datetime.fromtimestamp(now) - datetime.utcfromtimestamp(now)

            print(f"Next show time: {(next_time + offset).strftime('%Y-%m-%d %I:%M %p')}")
            print("Prize: " + response_data["nextShowPrize"])
            time.sleep(5)
    else:
        socket = response_data["broadcast"]["socketUrl"].replace("https", "wss")
        print(f"Show active, connecting to socket at {socket}")
        asyncio.get_event_loop().run_until_complete(networking.websocket_handler(socket, headers))
