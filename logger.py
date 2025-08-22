#!/bin/python3
from pathlib import Path
import logging

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
