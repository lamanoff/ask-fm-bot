# Ask FM Bot

## Description 
A simple bot that allows you to post a personal link where the user can receive anonymous messages through this bot and respond to them.

## Features
- Working with the MongoDB database - saving and deleting users and messages to implement analytics (you can use Redash for this).
- Welcome message with a picture (the picture is not in the repository).
- Sending texts, stickers, photos, videos, stories, voices, audios and documents.
- Checking for the subscription on channels.

## How to run
1. Install Python 3.
2. Install the requirements - `pip3 install -r requirements.txt`.
3. Create telegram bot with @BotFather.
4. Create MongoDB database.
5. Copy the API Token from @BotFather for the bot.
6. Copy the connection string for the database.
7. Set up the environment variables or instert data in the constants in code - `API_TOKEN`, `CONNECTION_STRING`.
8. Run the bot - `python3 main.py`.

Or use docker.
