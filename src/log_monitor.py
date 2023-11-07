import os
import re

from server_operations import send_message_to_player, send_to_discord

from config import DEFAULT_CONFIG

from logger import get_logger

logger = get_logger(__name__)

CONNECT_PATTERN = re.compile(r": (.*?) (joined|left) this ARK!")

class LogEventFactory:
    event_types = []

    @classmethod
    def register_event_type(cls, event_type):
        cls.event_types.append(event_type)

    @classmethod
    def create(cls, line) -> "LogEvent":
        for event_type in cls.event_types:
            if event_type.is_event(line):
                return event_type(line)
        return LogEvent(line)

class LogEvent:
    def __init__(self, line):
        self.line = line
        self.message = self._get_message()
        self._post_classification()

    def _get_message(self):
        parts = self.line.split(':')
        return ':'.join(parts[2:]).strip()

    def _post_classification(self):
        # This method will be called after an event has been classified.
        # It can be overridden by subclasses to perform specific actions.
        pass

    def __str__(self):
        return f"{self.message}"

class PlayerConnectEvent(LogEvent):

    def __init__(self, line):
        self.player_name, self.event_type = self._get_player_info(line)
        super().__init__(line)

    @staticmethod
    def _get_player_info(line):
        # logger.info(f"Searching for player info in {line} with REGEXP {CONNECT_PATTERN.pattern}")
        match = CONNECT_PATTERN.search(line)
        if match:
            return match.group(1), match.group(2)
        return None, None

    def _post_classification(self):
        if self.event_type == "joined":
            send_message_to_player(self.player_name, f'Welcome {self.player_name}! {DEFAULT_CONFIG["tasks"]["announcement"]["description"]}')
        elif self.event_type == "left":
            pass
        send_to_discord(f"{self.player_name} has {self.event_type} the server", "log_webhook")

    def __str__(self):
        return f"Player {self.event_type}: {self.player_name}"


class PlayerJoined(PlayerConnectEvent):
    @classmethod
    def is_event(cls, line):
        return "joined this ARK!" in line

class PlayerLeft(PlayerConnectEvent):
    @classmethod
    def is_event(cls, line):
        return "left this ARK!" in line


LogEventFactory.register_event_type(PlayerJoined)
LogEventFactory.register_event_type(PlayerLeft)

class LogMonitor:
    def __init__(self):
        self.filepath = f"{DEFAULT_CONFIG['server']['install_path']}\\ShooterGame\\Saved\\Logs\\ShooterGame.log"
        try:
            self.last_size = os.path.getsize(self.filepath)
        except FileNotFoundError:
            logger.error(f"Log file does not exist: {self.filepath}")
            self.last_size = 0

    def process_new_entries(self) -> list[LogEvent]:
        try:
            current_size = os.path.getsize(self.filepath)
        except FileNotFoundError:
            logger.error(f"Log file does not exist: {self.filepath}")
            return []

        if current_size == self.last_size:
            return []  # No new content

        new_entries = []
        try:
            with open(self.filepath, 'r') as file:
                file.seek(self.last_size)
                new_entries = file.readlines()
                self.last_size = current_size
        except FileNotFoundError:
            logger.error(f"Log file does not exist: {self.filepath}")
            # You might want to handle this differently if the file disappears mid-operation
        except OSError as e:
            logger.error(f"Error reading log file: {e}")

        log_events = [LogEventFactory.create(line) for line in new_entries]
        return log_events

# Usage
if __name__ == "__main__":
    log_file_path = 'path/to/your/logfile.log'  # Replace with your log file path
    monitor = LogMonitor(log_file_path)
    monitor.monitor()  # Starts the monitoring process
