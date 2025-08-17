import os
import sys
import requests
import asyncio
import aiohttp
from dotenv import load_dotenv


def login_access_token(login_url, username, password):
    headers = {
        "x-csrf-token": "1",
        "Content-Type": "application/json",
    }

    payload = {
        "user": username,
        "pass": password,
    }

    response = requests.post(login_url, headers=headers, json=payload)
    response.raise_for_status()

    data = response.json()
    token = data["data"]["sessionToken"]

    return token


async def listen_hackeychat(websocket_url, access_token, handler, retry_delay=5):
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(websocket_url) as ws:
                    await ws.send_json({"type": "session", "token": access_token})

                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            await handler(ws, msg.data)
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            print("WebSocket error:", msg.data)
                            break
                        elif msg.type == aiohttp.WSMsgType.CLOSED:
                            print("WebSocket closed by server")
                            break
        except aiohttp.ClientError as e:
            print(f"Connection error: {e}")
        except asyncio.CancelledError:
            break

        print(f"Reconnecting in {retry_delay} seconds...")
        await asyncio.sleep(retry_delay)


async def message_handler(websocket, message):
    try:
        print(message)
    except Exception as e:
        print(f"Handler exception: {e}")


if __name__ == "__main__":
    load_dotenv()

    username = os.environ.get("HACKEY_USER")
    password = os.environ.get("HACKEY_PASSWORD")
    login_url = os.environ.get("HACKEY_LOGIN_URL")
    websocket_url = os.environ.get("HACKEY_WEBSOCKET_URL")

    try:
        access_token = login_access_token(login_url, username, password)
    except:
        print("Could not login")
        sys.exit(1)

    asyncio.run(listen_hackeychat(websocket_url, access_token, message_handler))
