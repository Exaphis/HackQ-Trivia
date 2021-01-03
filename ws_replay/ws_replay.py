import aiohttp
from aiohttp import web
import pickle

msgs = []


async def ws_replay(request):
    global msgs

    ws = web.WebSocketResponse()
    await ws.prepare(request)

    for msg in msgs:
        if msg.type == aiohttp.WSMsgType.TEXT:
            await ws.send_str(msg.data)
        elif msg.type == aiohttp.WSMsgType.BINARY:
            await ws.send_bytes(msg.data)
        else:
            print(f'msg contains unimplemented frame of type {str(msg.type)}')
            print(msg)

    return ws


def main():
    global msgs
    with open('msgs2.pickle', 'rb') as msgs_in:
        msgs = pickle.load(msgs_in)
    print(msgs)

    app = web.Application()
    app.add_routes([web.get('/ws', ws_replay)])
    web.run_app(app)


if __name__ == '__main__':
    main()
