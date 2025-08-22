from codecs import ignore_errors
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
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

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
        
        
    # getters:
    def get_owner(self):
        return self._bot_owner

  
    # === Persistence ===
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
            cutoff = now + timedelta(minutes=self._WINDOW_MINUES)
            
            user_progress = self._progress.setdefault(user_id, {"guessed": [], "attempts": [], "themes": {}})
            attempts = [ts for ts in user_progress["attempts"] if datetime.fromisoformat(ts) < cutoff]

            if len(attempts) >= self._LIMIT_WINDOW:
                return False, cutoff.strftime("%H:%M:%S")

            attempts.append(now.isoformat())
            user_progress["attempts"] = attempts
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
        self._logger.info(f"Message from {message.author}: {message.content}")
        if message.author == self.user:
            return

        
        try:
            await self.random_message(message)   

            if message.content.startswith('!hello'):
                try:
                    await self.get_channel(self._channels["Botting"]).send('Hello World!') # type: ignore
                    self._logger.info(f"Command $hello$ executed.")
                except Exception as e:
                    self._logger.error(f"Error sending hello message: {e}")
            
            if message.channel.id == self._channels["Botting"]:
                user_id = str(message.author.id)
                
                guild_progress = self._progress.setdefault(
                    message.guild.id if message.guild is not None else 'guild', 
                    {"guessed": [], "attempts": [], "themes": {}}
                )
                
                user_progress = self._progress.setdefault(
                    user_id, 
                    {"guessed": [], "attempts": [], "themes": {}}
                )
                
                guessed_words = set(user_progress.get("guessed", []))
                guessed_words_guild = set(guild_progress.get("guessed", []))
                
                themes_progress = user_progress.get("themes", {})
                theme_progress_guild = guild_progress.get("themes", {})
                
                if message.content.startswith("!stats"):
                    try:
                        if "--guild" in message.content.lower():
                            self._logger.info(f"Sent guild stats")
                            returned_theme_status = "\n".join(
                                f"{theme}: {len(words)}/{len(self._THEMES[theme])}" 
                                for theme, words in theme_progress_guild.items()
                            )
                            progress_msg = f"Progress: {len(guessed_words_guild)}/{len(self._banned_words)} words.\n"
                        else:
                            self._logger.info(f"sent user stats")
                            returned_theme_status = "\n".join(
                                f"{theme}: {len(words)}/{len(self._THEMES[theme])}" 
                                for theme, words in themes_progress.items()
                            )
                            progress_msg = f"Progress: {len(guessed_words)}/{len(self._banned_words)} words."

                        await self.send_message(
                            message,
                            f"{progress_msg}\nTheme progress:\n{returned_theme_status}"
                        )
                    except Exception as e:
                        self._logger.error(f"Error sending progress message: {e}")

                
                if message.content.startswith("!guess"):
                    words_in_msg = set(re.findall(r"\b\w+\b", message.content.lower()))     
                    matches = self._banned_words & words_in_msg # Set intersection
                    if matches:
                        allowed, next_time = self.can_attempt(user_id)
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

                        new_guesses = matches - guessed_words
                        if new_guesses:
                            guessed_words.update(new_guesses)
                            user_progress["guessed"] = list(guessed_words)
                            guild_progress["guessed"] = list(guessed_words)
                            self.update_themes(user_progress, new_guesses)
                            self.update_themes(guild_progress, new_guesses)

                            try:
                                await self.send_message(
                                    message,
                                    f"Correct guesses: {', '.join(new_guesses)}\n"
                                )
                            except Exception as e:
                                self._logger.error(f"Error sending correct guesses message: {e}")

                            remaining = list(self._banned_words - guessed_words)
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


                self._progress[user_id] = user_progress
                self._progress[message.guild.id if message.guild is not None else 'guild'] = guild_progress
                self.save_progress()
                
        except Exception as e:
            self._logger.error(f"Error in on_message: {e}")


    # Random messages
    async def random_message(self, message):
        try:
            if random.randint(0, 84) == 42:
                msg = random.choice(config.SAD_MSGS)
                self._logger.info(f"sent message: {msg}")
                try:
                    await message.channel.send(msg)
                except Exception as e:
                    self._logger.error(f"Error sending random message: {e}")
        except Exception as e:
            self._logger.error(f"Error in random_message: {e}")


    # Other message checks
    async def message_check(self, message):
        try:
            unique_words = set(message.content.lower().split(" "))
            if self._easter_egg_word in unique_words:
                if self._easter_egg_count == 3:
                    self._easter_egg_count = 0
                    try:
                        await self.send_message(
                            message, 
                            f"I'm the ghost with the most, babe."
                        )
                    except Exception as e:
                        self._logger.error(f"Error sending Beetlejuice message: {e}")
                else:
                    self._easter_egg_count += 1

            if self._banned_words & unique_words:
                response = f"You're going to jail {message.author}"
                await self.send_message(
                    message, 
                    response
                )
        except Exception as e:
            self._logger.error(f"Error in message_check: {e}")


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
