import aiohttp
import asyncio
import os
import pickle
import signal

from hackq_trivia.config import config


terminate = False


def mark_terminate(signum, frame):
    global terminate
    terminate = True


async def ws_connect(uri, headers):
    global terminate
    session = aiohttp.ClientSession()
    msgs = []

    async with session.ws_connect(uri, headers=headers, heartbeat=5) as ws:
        # heartbeat?
        # await ws.send_str('echo test')

        while not terminate:
            try:
                msg = await ws.receive(timeout=5)
            except asyncio.exceptions.TimeoutError:
                print('timeout, retry')
                continue

            print(msg)
            if msg.type in (aiohttp.WSMsgType.CLOSED,
                            aiohttp.WSMsgType.CLOSING,
                            aiohttp.WSMsgType.ERROR):
                break
            else:
                msgs.append(msg)

    await session.close()

    return msgs


def next_fname(base_name):
    num = 1
    curr_name = base_name.format(num)
    while os.path.exists(curr_name):
        num += 1
        curr_name = base_name.format(num)

    return curr_name


def main():
    signal.signal(signal.SIGINT, mark_terminate)
    signal.signal(signal.SIGTERM, mark_terminate)

    bearer = config.get('CONNECTION', 'BEARER')
    headers = {
        'User-Agent': 'Android/1.40.0',
        'x-hq-client': 'Android/1.40.0',
        'x-hq-country': 'US',
        'x-hq-lang': 'en',
        'x-hq-timezone': 'America/New_York',
        'Authorization': f'Bearer {bearer}',
        # 'Connection': 'Upgrade'
    }
    uri = 'wss://ws.prod.hype.space/ws/52637?universal'

    loop = asyncio.get_event_loop()
    msgs = loop.run_until_complete(ws_connect(uri, headers))
    print(pickle.dumps(msgs))

    with open(next_fname('msgs{}.pickle'), 'wb') as out:
        pickle.dump(msgs, out)


if __name__ == '__main__':
    main()
