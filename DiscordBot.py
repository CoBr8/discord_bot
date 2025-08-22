#!/bin/python3
"""
name:   DiscordBot.py
date:   2025-08-21
auth:   CoBr8
desc:
    Class definition for a discord bot
"""
 
# system imports

import discord
import random
from discord.ext import commands
# locallt define config file
import config


class DiscordBot(commands.Bot):
    
    def __init__(self, token, logger, channels: dict):
        # applying the bots default intents
        intents = discord.Intents.default()
        # bot requires the message_content intent from the dev portal for discord apps.
        intents.message_content = True  # Required for reading messages
        # assigning the command prefix, and the bots required intents
        super().__init__(command_prefix="!", intents=intents)
        
        self.logger = logger
        self.__token = token
        self.__channels = channels
        self.__beetle_juice_counter = 0
    
    
    # function to handle message creation/send events.     
    async def on_message(self, message: discord.Message):
        # if the the message is from the bot, ignore it.
        if message.author != self.user:
            # save message to the log
            self.logger.info(f"Message from {message.author}: {message.content}")
            # check to see if a random message is being sent
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


    async def message_check(self, message):
        banned_words = set(config.BAN_WORDS)
        unique_words = set(message.content.lower().split(" "))
        
        if "beetlejuice" in unique_words:
            if self.__beetle_juice_counter == 3:
                self.__beetle_juice_counter = 0
                await self.get_channel(self.__channels["Botting"]).send(f"I'm the ghost with the most, babe.") # type: ignore
            else:
                self.__beetle_juice_counter += 1

        if banned_words & unique_words:
            response = f"You're going to jail {message.author}"
            await self.handle_message(message, response)
            
    async def troll_user(self, message):
         if message.author.id == config.user_ids[0]:
            await self.handle_message(message, )
            
    # function to handle sending messages
    async def handle_message(self, message, response=None):
       await self.get_channel(self.__channels["Botting"]).send(response) # type: ignore
    
    
    # Running the bot. 
    def run_bot(self):
        super().run(self.__token)


