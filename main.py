import os
import sys
import requests
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

    print(access_token)
