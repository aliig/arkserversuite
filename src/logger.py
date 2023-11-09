import logging
import os
import sys

from constants import OUTPUT_DIRECTORY

# Setting up logging
log_path = os.path.join(OUTPUT_DIRECTORY, "log.txt")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
)


# Custom class to redirect stdout and stderr to logger
class LoggerToFile:
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level

    def write(self, message):
        # Eliminate extra newlines in logger output
        if message != "\n":
            self.logger.log(self.level, message)

    def flush(self):
        pass  # Leave it empty to satisfy the stream interface


sys.stdout = LoggerToFile(logging.getLogger(), logging.INFO)
sys.stderr = LoggerToFile(logging.getLogger(), logging.ERROR)


def get_logger(name=None):
    return logging.getLogger(name)
