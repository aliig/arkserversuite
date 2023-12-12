import logging
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

import colorlog

from config import CONFIG, OUTDIR

# Retrieve log level from the configuration
log_level_str = CONFIG["advanced"].get("log_level", "info")
log_level = logging.DEBUG if log_level_str.lower() == "debug" else logging.INFO

# Setting up logging

log_path = os.path.join(OUTDIR, "log.txt")

# Define log colors
log_colors = {
    "DEBUG": "white",
    "INFO": "cyan",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "bold_red",
}

# Create a formatter that uses these colors
formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s [%(levelname)s]: %(message)s", log_colors=log_colors
)

# Create handlers for file and console
file_handler = logging.FileHandler(log_path, encoding="utf-8")  # specify encoding here
console_handler = colorlog.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)

logging.basicConfig(
    level=log_level,  # Use the log level from the config
    format="%(asctime)s [%(levelname)s]: %(message)s",
    handlers=[file_handler, console_handler],
)


# Custom class to redirect stdout and stderr to logger
class LoggerToFile:
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level

    def write(self, message):
        if message != "\n":
            self.logger.log(self.level, message)

    def flush(self):
        pass


sys.stdout = LoggerToFile(logging.getLogger(), log_level)
sys.stderr = LoggerToFile(logging.getLogger(), logging.ERROR)


def get_logger(name=None):
    return logging.getLogger(name)
