import os
import sys
import json
import re
import requests
import asyncio
import aiohttp
import random
import string
from dataclasses import dataclass
from imdb import imdb_info_by_id, imdb_info_by_search, imdb_printout

from dotenv import load_dotenv

load_dotenv()

import wolfram


#
# Chat Login
#


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


#
# Chat Websocket
#


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


#
# Send Chat
#


async def send_message(websocket, message_text):
    unique_id = "".join(random.choices(string.ascii_letters + string.digits, k=21))
    message_to_send = {
        "type": "msg",
        "id": unique_id,
        "text": message_text,
    }
    await websocket.send_str(json.dumps(message_to_send))


#
# Lmao Memes
#


cwd = os.path.dirname(os.path.abspath(__file__))
memes = {}
for filename in os.listdir(cwd):
    if filename[-10:] == "_memes.txt":
        meme_type = filename[:-10]
        memes[meme_type] = [line.rstrip("\n") for line in open(cwd + "/" + filename)]

with open(cwd + "/stash_memes.json", "r") as stashjson:
    stash_memes = json.load(stashjson)

roger_messages = [
    "I am here",
    "I'm here for you",
    "ayyyy lmaoo",
    "Let's get this bread",
    "What do you need?",
]

simple_memes: dict[str, str] = {
    "devil?": stash_memes["/devil?"],
    "go2bed": stash_memes["/go2bed"],
    "gil2bed": stash_memes["/gil2bed"],
}

random_memes: dict[str, list[str]] = {
    "lmao?": roger_messages,
    "ronaldo": memes["ronaldo"],
    "rolando": memes["ronaldo"],
    "penaldo": memes["ronaldo"],
    "milady": memes["milady"],
    "maga": memes["trump"],
    "biden": memes["biden"],
}


def random_selection(list):
    return list[random.randint(0, len(list) - 1)]


meme_cmds = "|".join(
    re.escape(cmd) for cmd in list(simple_memes.keys()) + list(random_memes.keys())
)
command_re = re.compile(meme_cmds, flags=re.IGNORECASE)
imdb_re = re.compile(r"(?:.*\.|.*)imdb.com/(?:t|T)itle(?:\?|/)(..\d+)")
bot_user_lower = "lmaolover"


#
# Message
#


@dataclass
class UserMessage:
    id: int
    time: int
    text: str
    user: str

    @staticmethod
    def from_json(json_str: str):
        data = json.loads(json_str)
        if data.get("type") != "msg":
            raise ValueError("Not a 'msg' type message")
        return UserMessage(
            id=data["id"],
            time=data["time"],
            text=data["text"],
            user=data["user"],
        )


#
# Message Responder
#


async def message_handler(websocket, message):
    try:
        try:
            msg = UserMessage.from_json(message)
        except ValueError:
            return

        print(f"<{msg.user}> {msg.text}")

        if msg.user.lower() == bot_user_lower:
            return

        message_body_lower = msg.text.lower()

        # Wolfram Alpha
        if (
            len(message_body_lower) > 2
            and message_body_lower[0] == "?"
            and message_body_lower[1] == "?"
            and message_body_lower[2] != "?"
        ):
            wolfram_response = wolfram.chatbot_wolfram_query(
                message_body_lower[2:].strip()
            )
            await send_message(websocket, wolfram_response)

        # IMDB search
        elif (
            imdb_matches := imdb_re.search(msg.text)
        ) or message_body_lower.startswith("!imdb "):
            try:
                if imdb_matches:
                    video_id = imdb_matches.group(1)
                    imdb_info = await asyncio.to_thread(imdb_info_by_id, video_id)
                else:
                    imdb_info = await asyncio.to_thread(
                        imdb_info_by_search, message_body_lower[6:40]
                    )
                    video_id = imdb_info["imdbID"]
                await send_message(
                    websocket, imdb_printout(imdb_info, show_poster=True)
                )
            except KeyError:
                await send_message(websocket, "Never heard of it")
            except requests.exceptions.Timeout:
                await send_message(websocket, "imdb ded")
            except requests.exceptions.HTTPError:
                await send_message(websocket, "imdb ded")

        # Memes
        elif command_matches := command_re.findall(msg.text):
            cmd_matches = [cmd.lower() for cmd in command_matches]
            # remove ticks from quoting
            cmd_matches = [s[:-1] if s.endswith("`") else s for s in cmd_matches]

            # Plural option
            cmds_expanded = []
            for match in cmd_matches:
                if (
                    match not in stash_memes
                    and match[-1] == "s"
                    and match[:-1] in stash_memes
                ):
                    cmds_expanded.extend([match[:-1]] * 3)
                elif (
                    match not in stash_memes
                    and match[-2:] == "es"
                    and match[:-2] in stash_memes
                ):
                    cmds_expanded.extend([match[:-2]] * 3)
                elif (
                    f"{match}s" in message_body_lower
                    or f"{match}es" in message_body_lower
                ):
                    cmds_expanded.extend([match] * 3)
                else:
                    cmds_expanded.append(match)

            if "spam" in message_body_lower:
                cmds_expanded = cmds_expanded * 3

            links = []
            for cmd in cmds_expanded:
                if cmd in simple_memes.keys():
                    links.append(simple_memes.get(cmd))
                elif cmd in random_memes.keys():
                    links.append(random_selection(random_memes.get(cmd)))

            cmd_msg = " ".join(links[:3])

            if cmd_msg.strip():
                await send_message(websocket, cmd_msg)

    except Exception as e:
        print(f"Handler exception: {e}")


#
# Main
#


if __name__ == "__main__":
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
