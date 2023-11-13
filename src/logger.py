import logging
import os
import sys

from constants import OUTPUT_DIRECTORY
from config import DEFAULT_CONFIG

# Retrieve log level from the configuration
log_level_str = DEFAULT_CONFIG["log_level"] if "log_level" in DEFAULT_CONFIG else "info"
log_level = logging.DEBUG if log_level_str.lower() == "debug" else logging.INFO

# Setting up logging
os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
log_path = os.path.join(OUTPUT_DIRECTORY, "log.txt")
logging.basicConfig(
    level=log_level,  # Use the log level from the config
    format="%(asctime)s [%(levelname)s]: %(message)s",
    handlers=[logging.FileHandler(log_path), logging.StreamHandler(sys.stdout)],
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
