# <img src="/pog.png" alt="Pog" width="40px" height="40px"> xchrombot

[xchrombot](https://github.com/chromium7/xchrombot) is an experimental Twitch chat bot built with Python. Features are currently still under developments.

## Installation
- Create a `config_local.py` file and define these two variables, replacing the `...` with the credentials for your bot's twitch account. You can generate your token here https://twitchapps.com/tmi/ while logged in to your chatbot account.

```
OAUTH_TOKEN="..."
TWITCH_USERNAME="..."
```

- Simply run `python main.py`


## Docker Installation

- docker build -t xchrombot .
- docker run -v ${PWD}:/app --name xchrombot-cont xchrombot


### Note
Python may not be the best language for a chatbot, but it allows for rapid development. While this chatbot works, it is more of an explorative project to familiarize myself with different APIs and twitch's IRC interface.
