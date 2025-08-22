#!/bin/python3
"""
name:   main.py
date:   2025-08-21
auth:   CoBr8
desc:
    Importing class modules and config information to generate main script body.
"""

from logger import Logger # logging class to handle server side logging
from DiscordBot import DiscordBot # DiscordBot class to handle Guild interactions
from pathlib import Path # pathlib > sys
from os import getpid
import logging # python logging module
import config # configuration file, local environment defined

def main():       
    # define path to where we want the log file to exist
    LOG_PTH = Path.cwd() / Path("LOGS/") / (__name__  + ".log")
    
    pid_file = LOG_PTH.parent.parent / Path("kill_bot.sh")
    pid_file.write_text(f"#!/bin/zsh\nkill {getpid()}")
    
    # generating out log object using custom logger class
    logs = Logger(__name__, LOG_PTH, logging.INFO)
    
    # inform log that we are starting the bot
    logs.info("Starting Discord Bot")
    
    # creating a bot object from the custom DiscordBot class
    bot = DiscordBot(config.TOKEN, logger=logs, channels=config.channels)
    
    # starting the bot to handle guild interactions
    bot.run_bot()
    
    
if __name__ == "__main__":
    main()
