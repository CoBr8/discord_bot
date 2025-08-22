from ast import arguments
from codecs import ignore_errors
import functools
import discord
import random
from discord.ext import commands
from pathlib import Path
import json
import re
from datetime import datetime, timedelta
import config

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
        self._easter_egg_word = config.EASTER_EGG_WORD
        
        
        self._words = config.WORDS
        self._THEMES = self._words
        self._banned_words = set(self._words['memes']) | \
                            set(self._words['tech'])  | \
                            set(self._words['gaming']) | \
                            set(self._words['mythology']) | \
                            set(self._words['trolling']) | \
                            set(self._words['international'])

        self._PROGRESS_FILE = Path.cwd() / Path("data/progress.json")
        self._PROGRESS_FILE.parent.mkdir(
            parents=True, 
            exist_ok=True
        )
        
        self._LIMIT_WINDOW = 10
        self._WINDOW_MINUES = 30
        
        self._progress = self.load_progress()
        
        self._bot_owner = config.OWNER
        self._commands = {
            "!guess" : self.guess_words,
            "!stats" : self.get_stats,
            "!hello" : self.hello_world,
        }
        
    
    async def guess_words(self, message):
        matches = self._banned_words & self._words_in_msg # Set intersection
        if matches:
            allowed, next_time = self.can_attempt(message.author.id)
            if not allowed:
                try:
                    await self.send_message(
                        message,
                        f"Out of guesses! Try again after {next_time}."
                    )
                except Exception as e:
                    self._logger.error(f"Error sending rate limit message: {e}")
                self.save_progress()
                return

            new_guesses = matches - self._guessed_words
            if new_guesses:
                self._guessed_words.update(new_guesses)
                self._user_progress["guessed"] = list(self._guessed_words)
                self._guild_progress["guessed"] = list(self._guessed_words)
                self.update_themes(self._user_progress, new_guesses)
                self.update_themes(self._guild_progress, new_guesses)

                try:
                    await self.send_message(
                        message,
                        f"Correct guesses: {', '.join(new_guesses)}\n"
                    )
                except Exception as e:
                    self._logger.error(f"Error sending correct guesses message: {e}")

                remaining = list(self._banned_words - self._guessed_words)
                if remaining:
                    try:
                        await self.send_message(
                            message,
                            f"Words are remaining still"
                        ) 
                    except Exception as e:
                        self._logger.error(f"Error sending hint message: {e}")
                else:
                    try:
                        await self.send_message(
                            message, 
                            f"Congratulations {message.author.name}! You guessed all the words!"
                        )
                    except Exception as e:
                        self._logger.error(f"Error sending completion message: {e}")
            else:
                try:
                    await self.send_message(
                        message, 
                        "You already guessed these words!"
                    )
                except Exception as e:
                    self._logger.error(f"Error sending duplicate guess message: {e}")


    async def get_stats(self, message):
        try:
            if "--guild" in message.content.lower():
                self._logger.info(f"Sent guild stats")
                returned_theme_status = "\n".join(
                    f"{theme}: {len(words)}/{len(self._THEMES[theme])}" 
                    for theme, words in self._theme_progress_guild.items()
                )
                progress_msg = f"Progress: {len(self._guessed_words_guild)}/{len(self._banned_words)} words.\n"
            else:
                self._logger.info(f"sent user stats")
                returned_theme_status = "\n".join(
                    f"{theme}: {len(words)}/{len(self._THEMES[theme])}" 
                    for theme, words in self._themes_progress.items()
                )
                progress_msg = f"Progress: {len(self._guessed_words)}/{len(self._banned_words)} words."

            await self.send_message(
                message,
                f"{progress_msg}\nTheme progress:\n{returned_theme_status}"
            )
        except Exception as e:
            self._logger.error(f"Error sending progress message: {e}")


    async def hello_world(self, message):
        try:
            await message.channel.send('Hello World!')
            self._logger.info(f"Command !hello executed.")
        except Exception as e:
            self._logger.error(f"Error sending hello message: {e}")


    # Getters
    def get_owner(self):
        return self._bot_owner

  
    # Persistence
    def load_progress(self):
        try:
            if self._PROGRESS_FILE.exists():
                self._logger.info(f"progress file exists, loading json.")
                return json.loads(self._PROGRESS_FILE.read_text())
        except Exception as e:
            self._logger.error(f"Failed to load progress: {e}")
        return {}


    def save_progress(self):
        try:
            self._PROGRESS_FILE.write_text(json.dumps(self._progress, indent=2))
            self._logger.info(f"Saving progress to file: {self._PROGRESS_FILE}")
        except Exception as e:
            self._logger.error(f"Failed to save progress: {e}")


    # Rate limiting
    def can_attempt(self, user_id):
        """
        pseudo:
            check time on message
            create time window -> time now + 30min
            
            check in window
                in window check if under guess limit
                    if under count attempt
                    if over respond.
                outside window respond
            
        """
        try:
            now = datetime.now()
            cutoff = now - timedelta(minutes=self._WINDOW_MINUES)
            
            self._user_progress = self._progress.setdefault(user_id, {"guessed": [], "attempts": [], "themes": {}})
            
            attempts = [ts for ts in self._user_progress["attempts"][::-1] if datetime.fromisoformat(ts) > cutoff]

            if len(attempts) >= self._LIMIT_WINDOW:
                return False, (datetime.fromisoformat("2025-08-22T12:57:29.095294") + timedelta(minutes=self._WINDOW_MINUES)).strftime("%H:%M:%S")
            else:
                attempts.append(now.isoformat())
                self._user_progress["attempts"] = attempts
                return True, None
        except Exception as e:
            self._logger.error(f"Error in rate limiting for user {user_id}: {e}")
            return False, "unknown"


    # Update theme progress
    def update_themes(self, progressions, new_words):
        try:
            themes_progress = progressions.setdefault("themes", {})
            for theme_name, theme_words in self._THEMES.items():
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


    # Message handling
    async def on_message(self, message: discord.Message):
        if message.author == self.user or message.author.id == self.get_user(268562382173765643):
            return
        
        self._logger.info(f"Message from {message.author}: {message.content}")
        
        self._words_in_msg = set(re.findall(r"\b\w+\b", message.content.lower()))
        
        try:
            await self.random_message(message)
            
            try:
                parts = message.content.lower().split(maxsplit=1)
                cmd = parts[0]
                args = parts[1] if len(parts)>1 else ""
                if cmd.startswith(self._command_char):             
                    func = self._commands.get(cmd)
                else:
                    func = False
                if args != "":
                    self._words_in_msg = set(re.findall(r"\b\w+\b", args))
                    
            except Exception as e: 
                self._words_in_msg = set(re.findall(r"\b\w+\b", message.content.lower()))
                func = False
            
            if self._easter_egg_word in self._words_in_msg:
                if self._easter_egg_count == 3:
                    self._easter_egg_count = 0
                    try:
                        await self.send_message(
                            message, 
                            f"I'm the ghost with the most, babe."
                        )
                        self._logger.info("Bot easter egg triggerd")
                    except Exception as e:
                        self._logger.error(f"Error sending Beetlejuice message: {e}")
                else:
                    self._easter_egg_count += 1    
            
            if message.channel.id == self._channels["Botting"]:
                user_id = str(message.author.id)
                self._guild_progress = self._progress.setdefault(
                    message.guild.id if message.guild is not None else 'guild', 
                    {"guessed": [], "attempts": [], "themes": {}}
                )
                self._user_progress = self._progress.setdefault(
                    user_id, 
                    {"guessed": [], "attempts": [], "themes": {}}
                )
                
                self._guessed_words = set(self._user_progress.get("guessed", []))
                self._guessed_words_guild = set(self._guild_progress.get("guessed", []))
                
                self._themes_progress = self._user_progress.get("themes", {})
                self._theme_progress_guild = self._guild_progress.get("themes", {})
                
                if func != False:
                    await func(message) # type: ignore

                self._progress[user_id] = self._user_progress
                self._progress[message.guild.id if message.guild is not None else 'guild'] = self._guild_progress
                self.save_progress()
                
        except Exception as e:
            self._logger.error(f"Error in on_message: {e}")


    # Random messages
    async def random_message(self, message):
        try:
            if random.randint(0, 84) == 42:
                msg = random.choice(config.SAD_MSGS)
                self._logger.info(f"Sent random message: {msg}")
                try:
                    await message.channel.send(msg)
                except Exception as e:
                    self._logger.error(f"Error sending random message: {e}")
        except Exception as e:
            self._logger.error(f"Error in random_message: {e}")


    # Generic message sender
    async def send_message(self, message, response=None):
        if response:
            try:
                await self.get_channel(self._channels["Botting"]).send(response) # type: ignore
                self._logger.info(f"Bot response: {response};to message: {message}")
            except Exception as e:
                self._logger.error(f"Error in send_message: {e}")


    # Run bot
    def run_bot(self):
        try:
            super().run(self._token)
        except Exception as e:
            self._logger.error(f"Error starting the bot. {e}")

