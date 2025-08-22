import discord
import random
from discord.ext import commands
from pathlib import Path
import json
import re
from datetime import datetime, timedelta
import config
import logging


class DiscordBot(commands.Bot):
    def __init__(self, token, logger, channels: dict):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

        self.logger = logger
        self.__token = token
        self.__channels = channels
        self.__beetle_juice_counter = 0
        self.__words = config.WORDS
        self.banned_words = set(self.__words['memes']) | set(self.__words['tech']) | set(self.__words['gaming'])
        self.THEMES = self.__words

        self.PROGRESS_FILE = Path("progress.json")
        self.LIMIT_PER_WINDOW = 10
        self.WINDOW_MINUTES = 30
        self.progress = self.load_progress()

    # === Persistence ===
    def load_progress(self):
        try:
            if self.PROGRESS_FILE.exists():
                return json.loads(self.PROGRESS_FILE.read_text())
        except Exception as e:
            self.logger.error(f"Failed to load progress: {e}")
        return {}

    def save_progress(self):
        try:
            self.PROGRESS_FILE.write_text(json.dumps(self.progress, indent=2))
        except Exception as e:
            self.logger.error(f"Failed to save progress: {e}")

    # === Rate limiting ===
    def can_attempt(self, user_id):
        try:
            now = datetime.now()
            cutoff = now - timedelta(minutes=self.WINDOW_MINUTES)
            user_progress = self.progress.setdefault(user_id, {"guessed": [], "attempts": [], "themes": {}})
            attempts = [ts for ts in user_progress["attempts"] if datetime.fromisoformat(ts) > cutoff]

            if len(attempts) >= self.LIMIT_PER_WINDOW:
                return False, (cutoff + timedelta(minutes=self.WINDOW_MINUTES)).strftime("%H:%M:%S")

            attempts.append(now.isoformat())
            user_progress["attempts"] = attempts
            return True, None
        except Exception as e:
            self.logger.error(f"Error in rate limiting for user {user_id}: {e}")
            return False, "unknown"

    # === Update theme progress ===
    def update_themes(self, user_progress, new_words):
        try:
            themes_progress = user_progress.setdefault("themes", {})
            for theme_name, theme_words in self.THEMES.items():
                theme_set = set(theme_words)
                guessed_in_theme = set(themes_progress.get(theme_name, []))
                newly_guessed = theme_set & new_words - guessed_in_theme
                if newly_guessed:
                    guessed_in_theme.update(newly_guessed)
                    themes_progress[theme_name] = list(guessed_in_theme)
            return themes_progress
        except Exception as e:
            self.logger.error(f"Error updating themes: {e}")
            return user_progress.get("themes", {})

    # === Message handling ===
    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        try:
            self.logger.info(f"Message from {message.author}: {message.content}")
            await self.random_message()
            await self.message_check(message)

            if message.content.startswith('$hello$'):
                try:
                    await self.get_channel(self.__channels["Botting"]).send('Hello World!') # type: ignore
                except Exception as e:
                    self.logger.error(f"Error sending hello message: {e}")

            user_id = str(message.author.id)
            user_progress = self.progress.setdefault(user_id, {"guessed": [], "attempts": [], "themes": {}})
            guessed_words = set(user_progress.get("guessed", []))

            words_in_msg = set(re.findall(r"\b\w+\b", message.content.lower()))
            matches = self.banned_words & words_in_msg

            if matches:
                allowed, next_time = self.can_attempt(user_id)
                if not allowed:
                    try:
                        await self.get_channel(self.__channels["Botting"]).send(f"Out of guesses! Try again after {next_time}.") # type: ignore
                    except Exception as e:
                        self.logger.error(f"Error sending rate limit message: {e}")
                    self.save_progress()
                    return

                new_guesses = matches - guessed_words
                if new_guesses:
                    guessed_words.update(new_guesses)
                    user_progress["guessed"] = list(guessed_words)

                    self.update_themes(user_progress, new_guesses)

                    themes_progress = user_progress.get("themes", {})
                    theme_status = "\n".join(
                        f"{theme}: {len(words)}/{len(self.THEMES[theme])}" 
                        for theme, words in themes_progress.items()
                    )

                    try:
                        await self.get_channel(self.__channels["Botting"]).send( # type: ignore
                            f"Correct guesses: {', '.join(new_guesses)}\n"
                            f"Progress: {len(guessed_words)}/{len(self.banned_words)} words.\n"
                            f"Theme progress:\n{theme_status}"
                        )
                    except Exception as e:
                        self.logger.error(f"Error sending progress message: {e}")

                    remaining = list(self.banned_words - guessed_words)
                    if remaining:
                        try:
                            await self.get_channel(self.__channels["Botting"]).send(f"Words remaining still.") # type: ignore
                        except Exception as e:
                            self.logger.error(f"Error sending hint message: {e}")
                    else:
                        try:
                            await self.get_channel(self.__channels["Botting"]).send( # type: ignore
                                f"Congratulations {message.author.name}! You guessed all the words!"
                            )
                        except Exception as e:
                            self.logger.error(f"Error sending completion message: {e}")
                else:
                    try:
                        await self.get_channel(self.__channels["Botting"]).send("You already guessed these words!") # type: ignore
                    except Exception as e:
                        self.logger.error(f"Error sending duplicate guess message: {e}")

            self.progress[user_id] = user_progress
            self.save_progress()
        except Exception as e:
            self.logger.error(f"Error in on_message: {e}")

    # === Random messages ===
    async def random_message(self):
        try:
            if random.randint(0, 84) == 42:
                msg = random.choice(config.SAD_MSGS)
                self.logger.info(f"sent message: {msg}")
                try:
                    await self.get_channel(self.__channels["Botting"]).send(msg) # type: ignore
                except Exception as e:
                    self.logger.error(f"Error sending random message: {e}")
        except Exception as e:
            self.logger.error(f"Error in random_message: {e}")

    # === Other message checks ===
    async def message_check(self, message):
        try:
            unique_words = set(message.content.lower().split(" "))
            if "beetlejuice" in unique_words:
                if self.__beetle_juice_counter == 3:
                    self.__beetle_juice_counter = 0
                    try:
                        await self.get_channel(self.__channels["Botting"]).send(f"I'm the ghost with the most, babe.") # type: ignore
                    except Exception as e:
                        self.logger.error(f"Error sending Beetlejuice message: {e}")
                else:
                    self.__beetle_juice_counter += 1

            if self.banned_words & unique_words:
                response = f"You're going to jail {message.author}"
                await self.handle_message(message, response)
        except Exception as e:
            self.logger.error(f"Error in message_check: {e}")

    # === Generic message sender ===
    async def handle_message(self, message, response=None):
        if response:
            try:
                await self.get_channel(self.__channels["Botting"]).send(response) # type: ignore
            except Exception as e:
                self.logger.error(f"Error in handle_message: {e}")

    # === Run bot ===
    def run_bot(self):
        try:
            super().run(self.__token)
        except Exception as e:
            self.logger.error(f"Failed to run bot: {e}")
