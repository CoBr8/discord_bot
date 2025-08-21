#!/bin/python3
"""
name:   DiscordBot.py
auth:   CoBr
date:   2025-08-19
desc:
    Using discord library to make a discord application (bot) to troll some folks in a private discord
"""
# system imports
import logging
import discord
import random

from discord.ext import commands
from pathlib import Path

import config


class Logger:
    def __init__(self, name: str, log_file: Path | None, level=logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False  # Prevent duplicate logs if root logger is configured

        # Formatter with timestamp + log level + message
        formatter = logging.Formatter(
            fmt="[%(asctime)s] | [%(levelname)s] | [%(name)s] | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Console handler (stdout by default)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)

        # Optional file handler
        if log_file:
            log_file = Path(log_file)  # ensure it's a Path
            log_file.parent.mkdir(parents=True, exist_ok=True)  # create parent dirs if missing
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self.logger.critical(msg, *args, **kwargs)
        

class DiscordBot(commands.Bot):
    def __init__(self, token, logger, channels: dict):
        intents = discord.Intents.default()
        intents.message_content = True  # Required for reading messages

        super().__init__(command_prefix="!", intents=intents)
        
        self.logger = logger
        self.__token = token
        self.__channels = channels
        self.__beetle_juice_counter = 0
    
    
    # function to handle message creation/send events.     
    async def on_message(self, message: discord.Message):
        if message.author != self.user:
            self.logger.info(f"Message from {message.author}: {message.content}")
            await self.random_message()
            await self.handle_message(message)

        if message.content.startswith('$hello'):
            await message.channel.send('Hello World!')
    
    
    # function to send random messages on event
    async def random_message(self):
        if random.randint(0,84) == 42:
            msg = random.choice(config.SAD_MSGS)
            self.logger.info(f"sent message: {msg}")
            await self.get_channel(self.__channels["Botting"]).send(msg) # type: ignore

    
    # function to handle sending messages
    async def handle_message(self, message):
        banned_words = set(config.BAN_WORDS)
        unique_words = set(message.content.lower().split(" "))
        
        if "beetlejuice" in unique_words:
            if self.__beetle_juice_counter == 3:
                self.__beetle_juice_counter = 0
                await self.get_channel(self.__channels["Botting"]).send(f"I'm the ghost with the most, babe.") # type: ignore
            else:
                self.__beetle_juice_counter += 1

        if banned_words & unique_words:
            await self.get_channel(self.__channels["Botting"]).send(f"You're going to jail {message.author}") # type: ignore
    
    
    # Running the bot. 
    def run_bot(self):
        super().run(self.__token)


def main():       
    
    LOG_PTH = Path.cwd() / Path("LOGS/") / __name__
    logs = Logger(__name__, LOG_PTH, logging.INFO)
    logs.info("Starting Discord Bot")

    bot = DiscordBot(config.TOKEN, logger=logs, channels=config.channels)
    
    bot.run_bot()
    
    
if __name__ == "__main__":
    main()
