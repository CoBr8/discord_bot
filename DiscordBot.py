import discord
import random
import json
import re

from discord.ext import commands
from pathlib import Path
from datetime import datetime, timedelta

import config
from AutoDict import AutoDict


class DiscordBot(commands.Bot):
    """
    name:   DiscordBot: Class
    auth:   CoBr8
    date:   2025-08-19
    desc:   
        Custom python class for a discord bot.
    """


    def __init__(self, token, logger, channels: dict):
        self._command_char = "!"
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=self._command_char, intents=intents)

        self._logger = logger
        self._token = token
        
        
        self._channels = channels
        self._easter_egg_count = 0
        self._easter_egg_word = config.settings.setdefault("EASTER_EGG_WORD", "Fourier")
        
        
        self._words = config.settings.setdefault("WORDS", {})
        self._banned_words = set(self._words['memes']) | \
                            set(self._words['tech'])  | \
                            set(self._words['gaming']) | \
                            set(self._words['mythology']) | \
                            set(self._words['trolling']) | \
                            set(self._words['international']) | \
                            set(self._words['life'])


        self._PROGRESS_FILE = Path.cwd() / Path("data/progress.json")
        
        if not self._PROGRESS_FILE.exists():
            self._logger.info(f"created progress file {self._PROGRESS_FILE =!s}")
            self._PROGRESS_FILE.touch()
        
        self._PROGRESS_FILE.parent.mkdir(
            parents=True, 
            exist_ok=True
        )
        
        self._LIMIT_WINDOW = 10
        self._WINDOW_MINUES = 30
        self._hydration_threshold = (
            config.settings.setdefault("HYDRATION", {})
            ).setdefault("WINDOW", 360) 
        
        self._progress = self.load_progress()
        
        self._bot_owner = config.settings.setdefault("OWNER", "")
        
        self._commands = {
            "!guess" : self.guess_words,
            "!stats" : self.get_stats,
            "!hello" : self.hello_world,
        }
        
    
    # Getters
    def get_owner(self):
        return self._bot_owner

  
    # Persistence
    def load_progress(self):
        try:
            if self._PROGRESS_FILE.exists():
                self._logger.info(f"Progress file exists, loading json.")
                progress_data = self._PROGRESS_FILE.read_text()
                if progress_data != "": 
                    return json.loads(progress_data)
                else:
                    return {}
        except Exception as e:
            self._logger.error(f"Failed to load progress: {e}")
        return {}
        
        
    def save_progress(self):
        try:
            with self._PROGRESS_FILE.open('w') as fp:
                json.dump(self._progress, fp=fp, indent=4)
            self._logger.info(f"Saving progress to file: {self._PROGRESS_FILE}")
        except Exception as e:
            self._logger.error(f"Failed to save progress: {e}")


    # Update theme progress
    def update_themes(self, progressions, new_words):
        try:
            themes_progress = progressions.setdefault("themes", {})
            for theme_name, theme_words in self._words.items():
                theme_set = set(theme_words)
                guessed_in_theme = set(themes_progress.get(theme_name, []))
                newly_guessed = theme_set & new_words - guessed_in_theme
                if newly_guessed:
                    guessed_in_theme.update(newly_guessed)
                    themes_progress[theme_name] = list(guessed_in_theme)
            return themes_progress
        except Exception as e:
            self._logger.error(f"Error updating themes: {e}")
            return progressions.get("themes", {})


    def split_message(self, message):
        func = False
        word_set = set()
        try:
            parts = message.content.lower().split(maxsplit=1)
            
            # get 'cmd' if it exists, otherwise false
            cmd = parts[0]
            if cmd.startswith(self._command_char):             
                func = self._commands.setdefault(cmd, self._logger.info)
                # if we have a command and args extract words.
                args = parts[1] if len(parts)>1 else ""
                if args != "": 
                    word_set = set(re.findall(r"\b\w+\b", args)) 
            else:
                word_set = set(re.findall(r"\b\w+\b", message.content.lower()))
        except Exception as e:
            word_set = set(re.findall(r"\b\w+\b", message.content.lower()))
        
        return func, word_set


    def guess_words(self, message):
        matches = self._banned_words & self._words_in_msg # Set intersection
        response = ""
        
        if matches:
            new_guesses = matches - self._guessed_words
            
            if new_guesses:
                self._guessed_words.update(new_guesses)
                self._user_progress["guessed"].extend(list(new_guesses))
                self._guild_progress["guessed"].extend(list(new_guesses))
                self.update_themes(self._user_progress, new_guesses)
                self.update_themes(self._guild_progress, new_guesses)

                response += f"Correct guesses: {', '.join(new_guesses)}\n"
                remaining = list(self._banned_words - self._guessed_words)

                if remaining:
                    response += "Words are remaining still"
                else:
                    response += f"Congratulations {message.author.name}! You guessed all the words!"
            else:
                response += "You already guessed these words!"
        return response


    def easter_egg(self, word_set):
        if self._easter_egg_word in word_set:
            if self._easter_egg_count == 3:
                self._easter_egg_count = 0
                self._logger.info("Bot easter egg triggerd")
                return True, f"I'm the ghost with the most, babe."
            else:
                self._easter_egg_count += 1
        return False,""
    
    
    def get_stats(self, message):
        try:
            if "--guild" in message.content.lower():
                
                self._logger.info(f"Sent guild stats")
                
                returned_theme_status = "\n".join(
                    f"{theme}: {len(words)}/{len(self._words[theme])}" 
                    for theme, words in self._theme_progress_guild.items()
                )
                
                progress_msg = f"Guild progress: {len(self._guessed_words_guild)}/{len(self._banned_words)} words.\n"
            else:
                self._logger.info(f"Sent user stats")
                returned_theme_status = "\n".join(
                    f"{theme}: {len(words)}/{len(self._words[theme])}" 
                    for theme, words in self._themes_progress.items()
                )
                progress_msg = f"{str(message.author.name)}'s progress: {len(self._guessed_words)}/{len(self._banned_words)} words.\n"
            return progress_msg + "Theme stats:\n" + returned_theme_status
        except Exception as e:
            self._logger.error(f"Error sending progress message: {e}")
            return None


    def hydration_reminder(self):
        self._logger.debug(f"START of hydration_reminder function")
        try:
            time_now    = datetime.now()
            
            time_path   = Path().cwd() / Path("data/hydro_homie")
            if not time_path.exists():
                time_path.parent.mkdir(
                    parents=True,
                    exist_ok=True
                )
                time_path.touch(exist_ok=True)
                time_path.write_text(time_now.isoformat())
                time_then = datetime(year=1969,month=12,day=1,hour=0,minute=0,second=0,microsecond=0)
            else:
                time_then = datetime.fromisoformat(time_path.read_text().strip())
            
            time_since = time_now - time_then
            TIMEDELTA_THRESHOLD = timedelta(minutes=self._hydration_threshold)
            
            if time_since > TIMEDELTA_THRESHOLD:
                time_path.write_text(time_now.isoformat())
                self._logger.debug(f"END of hydration_reminder function. Reminder sent")
                return f"Please drink some water."
            
        except Exception as e:
            self._logger.error(f"Error with hydration: {e!r}")
        self._logger.debug(f"END of hydration_reminder function. Exception caught. Error on previous line.")
        return ""


    def hello_world(self, message):
        try:
            self._logger.info(f"Command !hello executed.")
            return f'Hello World!'
        except Exception as e:
            self._logger.error(f"Error sending hello message: {e}")


    def check_words(self, word_set:set):
        self._logger.debug(f"check_words config 'ban': {set(config.settings.setdefault("BAN", []))}")
        self._logger.debug(f"check_words word_set: {word_set}")
        conditional_set = set(config.settings.setdefault("BAN", [])) & set(word_set)
        self._logger.debug(f"check_words set intersection: {conditional_set}")
        if conditional_set:
            return True, f"Where's my bike?"
        return False, ""            
    
    
    def message_json(self, message:discord.Message):
        """
        json data format:
        {
            "date": {
              "author": {
                  "timestamp": {
                      <content>
                    }
                }  
            },
        }
        
        """
        data_path = Path().cwd() / Path("data") / Path("messages.json")
        self._logger.debug(f"loading: {data_path = !s}")
        data_path.parent.mkdir(
            parents=True, 
            exist_ok=True
        )
        
        if not data_path.exists():
            data_path.touch()
        
        else: 
            try:
                file_text = data_path.read_text()
                self._logger.debug(f"Read file {data_path = !s}")
                
                if file_text:
                    json_data = json.loads(file_text)
                    self._logger.debug(f"converted file to Python 'JSON'")
                else:
                    self._logger.debug(f"File empty, creating dict")
                    json_data = AutoDict()
                
                date = str(datetime.now().strftime("%Y-%m-%d"))
                author_id = str(message.author.id)
                timestamp = str(message.created_at.isoformat())
                msg_text = str(message.clean_content)
                
                ((json_data.setdefault(date,{})).setdefault(author_id,{})).setdefault(timestamp, {})
                json_data[date][author_id][timestamp] = msg_text
                data_path.write_text(
                    json.dumps(
                        json_data, 
                        indent=4
                    )
                )
                self._logger.info(f"Wrote {message.id!s} to {data_path!s}")    
            # except 
            except json.JSONDecodeError:
                self._logger.error(f"Error decoding JSON file: {data_path = !s}")
                
            except Exception as e:
                self._logger.error(f"Unknown error: {e}")
            


    # On new message creation/send handling
    async def on_message(self, message: discord.Message):
        """
        name:   on_message
        auth:   CoBr8
        desc:
            When the guild receives a message this method deals with it
        """
        # log messages
        self.message_json(message=message)
        
        # check whether a bot or system has sent the message.
        if message.author.bot or message.author.system:
            # do nothing and end the event.
            return
        
        # using regular expressions to find all words in message
        self._words_in_msg = set(re.findall(r"\b\w+\b", message.content.lower()))
        
        # getting user and guild specific ID's to use as keys.
        user_id = str(message.author.id)
        guild_id = str(message.guild.id) if message.guild is not None else "guild"
            
        try:
            # random message response
            await self.random_message(message)
            
            # check if it times for a hydration reminder
            hydrate_message = self.hydration_reminder()
            if hydrate_message: # if "non-empty" object
                # send a message to the main channel to remind folks to hydrate. 
                await self.send_message(response=hydrate_message, channel="Main")
        
            # check if Bot is mentioned: 
            if self.user.mentioned_in(message): # type: ignore
                # if everyone is mentioned we don't need a bot responding. 
                if "everyone" in message.mentions:
                    # log everyone mention event.
                    self._logger.info(f"Everyone mentioned: {message.author.name =!s}")
                else:
                    # if swearing at bot, swear back.
                    if "fuck you" in message.content.lower(): 
                        await message.reply(config.settings.get("DIRECT_MESSAGE","").get("ANGRY"))
                    # if just mentioning bot, "humour" response.
                    else:
                        await message.reply(config.settings.get("DIRECT_MESSAGE","").get("NORMAL"))
                    
            func, word_set = self.split_message(message)
            
            ban, response = self.check_words(self._words_in_msg)
            
            if ban:
                await message.delete()
                await message.channel.send(response)
                
            egg, text = self.easter_egg(word_set=word_set)
            
            if egg:
                await self.send_message(response=text)
            
            if message.channel.id == self._channels["Botting"]:
                
                self._guild_progress = self._progress.setdefault(
                    guild_id,
                    {"guessed": [], "attempts": [], "themes": {}}
                )
                self._user_progress = self._progress.setdefault(
                    user_id, 
                    {"guessed": [], "attempts": [], "themes": {}}
                )
    
                self._guessed_words = set(self._user_progress.get("guessed", []))            
                self._themes_progress = self._user_progress.get("themes", {})
                
                self._guessed_words_guild = set(self._guild_progress.get("guessed", []))
                self._theme_progress_guild = self._guild_progress.get("themes", {})
                
                if func is not False:
                    response = func(message)
                    if response:
                        await self.send_message(response=response)
                        await message.delete(delay=3)

                self._progress[user_id] = self._user_progress        
                self._progress[guild_id] = self._guild_progress
        
                self.save_progress()
                
        except Exception as e:
            self._logger.error(f"Error in on_message: {e}")


    # Random messages
    async def random_message(self, message):
        try:
            if random.randint(0, 84) == 42:
                msg = random.choice(config.settings.setdefault("SAD_MSGS", []))
                self._logger.info(f"Bot sent random message: {msg}")
                try:
                    await message.channel.send(msg)
                except Exception as e:
                    self._logger.error(f"Error sending random message: {e}")
        except Exception as e:
            self._logger.error(f"Error in random_message: {e}")


    # Message sender
    async def send_message(self, response=None, channel="Botting"):
        if response:
            try:
                await self.get_channel(self._channels[channel]).send(response) # type: ignore
                self._logger.info(f"Bot sent response {response!r}")
            except Exception as e:
                self._logger.error(f"Error in send_message: {e}")


    # Run bot
    def run_bot(self):
        try:
            super().run(self._token)
        except Exception as e:
            self._logger.error(f"Error starting the bot. {e}")
