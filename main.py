#!/bin/python3
"""
name:   discord_bot
auth:   CoBr
date:   2025-08-19
desc:
    Using discord library to make a discord application (bot) to troll some folks in a private discord
"""

from logger import Logger
from DiscordBot import DiscordBot
from pathlib import Path
import logging
import config

def main():       
    
    LOG_PTH = Path.cwd() / Path("LOGS/") / __name__
    logs = Logger(__name__, LOG_PTH, logging.INFO)
    logs.info("Starting Discord Bot")

    bot = DiscordBot(config.TOKEN, logger=logs, channels=config.channels)
    
    bot.run_bot()
    
    
if __name__ == "__main__":
    main()
