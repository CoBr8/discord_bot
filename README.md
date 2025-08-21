# Discord_bot
## Auth: Colton Broughton

## Description

DiscordBot is a lightweight Discord bot designed to demonstrate custom logging, message handling, and fun interactive behavior inside a Discord server.

The bot can:

* Log activity to both console and file.
* Respond to simple commands (e.g., `$hello`).
* Randomly send messages from a predefined list.
* Monitor for banned words and react accordingly.
* Include an Easter egg triggered by repeated mentions of "beetlejuice."

This project is a starting point for experimenting with Discord bots using Python and [discord.py](https://discordpy.readthedocs.io/). It can be extended with additional commands and features.

---

## Badges

You can add badges here (build status, code coverage, Python version support, etc.) using [Shields.io](https://shields.io/).

---

## Visuals

Screenshots or terminal session GIFs can be included here if desired. For example, a screenshot of DiscordBot responding in a channel.

---

## Installation

### Requirements

* Python 3.10+
* `discord.py`
* A Discord bot token (from the [Discord Developer Portal](https://discord.com/developers/applications))

### Steps

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/nickbot.git
   cd nickbot
   ```

2. Install dependencies:

   ```bash
   pip install discord.py
   ```

3. Create a `config.py` file in the project root.
   **This file is not included in the repository and must be created by you.**

   At minimum, it must contain values for:

   * Your bot token
   * Channel IDs
   * Banned words
   * Sad messages

4. Run the bot:

   ```bash
   python main.py
   ```

---

## Usage

* **Check if the bot is online**
  Type:

  ```
  $hello
  ```

  The bot will respond with:

  ```
  Hello World!
  ```

* **Random messages**
  Occasionally, the bot will send one of the `SAD_MSGS` into your configured channel.

* **Banned words**
  If a user types a word from `BAN_WORDS`, the bot will respond with:

  ```
  You're going to jail <username>
  ```

* **Beetlejuice Easter Egg**
  Mentioning “beetlejuice” three times in a row will trigger:

  ```
  I'm the ghost with the most, babe.
  ```

---

## Support

If you encounter issues:

* Open an issue in this repository.
* Consult the [discord.py documentation](https://discordpy.readthedocs.io/).
* Double-check your `config.py` values.

---

## Roadmap

Planned improvements:

* Add more configurable triggers and responses.
* Implement persistent storage (e.g., database).
* Expand logging to structured formats (e.g., JSON).

---

## Contributing

Contributions are welcome!

1. Fork the repo.
2. Create a new branch for your feature/bugfix.
3. Submit a pull request.

Before contributing, please ensure your changes:

* Run without errors.
* Follow Python best practices (PEP8).
* Include documentation for new features.

---

## Authors and Acknowledgment

* Author: Colton Broughton
* Thanks to the maintainers of [discord.py](https://github.com/Rapptz/discord.py).

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

## Project Status

"Active" — under development and open to contributions.

---

## Example `config.py`

```python
# config.py
# Example configuration file for DiscordBot.
# You must provide your own values here.

# Discord bot token (from the Discord Developer Portal)
TOKEN = "your-bot-token-here"

# Channels the bot should use (replace with real channel IDs from your server)
channels = {
    "Botting": 123456789012345678  # Example channel ID
}

# List of banned words (the bot will respond if these are used)
BAN_WORDS = [
    "badword1",
    "badword2",
    "anotherword"
]

# List of random sad messages the bot may send occasionally
SAD_MSGS = [
    "I'm feeling a bit down today.",
    "Not every day is great, but I'm still here.",
    "Sometimes, silence is the loudest response.",
    "Do robots dream of electric sheep?"
]
```

