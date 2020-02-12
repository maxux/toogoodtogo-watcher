# TooGoodToGo Watcher

Python watcher for TooGoodToGo.

# Features

- Few dependencies (`requests`, `python-telegram-bot`)
- Fetching updates with random time update
- Night mode which prevent fetching during the night
- Speedup mode which fetch more quickly for specific time range
- Send notifications using Telegram Bot
- Console listing

# Setup

## Configure your account

Create a new account dedicated, login with this account on your phone. Setup your favorites merchant on the app.

## Configure the watcher

Copy the `config.sample.py` to `config.py` and update:
- Set your credentials
- Set coordinates for distance computing
- Normal wait time are random range for default fetch
- Speedup time and wait defines time range and wait range for speedup period
- Pause fields set night mode which disable fetch during night
- Telegram token and chatid for notification

# Telegram Bot

Setup your Telegram Bot by talking to `@BotFather`, then set your token on the config.
Create a group and join it, joins your bot on this group. Then vists `https://api.telegram.org/bot<TOKEN>/getUpdates` to get your `chat_id`.

# Source
Based on [marklagendijk/node-toogoodtogo-watcher](https://github.com/marklagendijk/node-toogoodtogo-watcher) version
but written in python with few depencencies and extra features.
