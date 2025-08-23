## Install and Run

You have Python 3 installed.

Install the requirements system wide:

```
pip install -r requirements.txt
```

or use a virtual environment or `uv` project tool for proper installation.

Run the bot:

```
python main.py
```

## Configure

Create a file `.env` and insert the correct information:

```
HACKEY_USER=...
HACKEY_PASSWORD=...
HACKEY_LOGIN_URL=...
HACKEY_WEBSOCKET_URL=...
```

## Meme Files

Create a file `stash_memes.json` like this:

```
{
  "/jeb": "https://i.imgur.com/iLvHHQO.jpeg",
  "/helper": "https://i.imgur.com/Pl8k3Mb.png"
}
```

The bot will respond to those commands (only works if it starts with `/`).

### Random Memes

Create any file named `something_memes.txt` with only plain links on each line.  You can access the links in the code using `memes["something"]`.
