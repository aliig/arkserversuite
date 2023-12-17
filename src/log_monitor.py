import os
import re
from collections import namedtuple

from config import CONFIG
from logger import get_logger
from rcon import get_active_players, send_message_to_player, send_to_discord

logger = get_logger(__name__)


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
        self.message = self._get_message(line)
        self._post_classification()

    @staticmethod
    def _get_message(line):
        parts = line.split(":")
        return ":".join(parts[2:]).strip()

    def _post_classification(self):
        # This method will be called after an event has been classified.
        # It can be overridden by subclasses to perform specific actions.
        pass

    def __str__(self):
        return f"{self.message}"


class PlayerConnectEvent(LogEvent):
    regexp_pattern = re.compile(r": (.*?) (joined|left) this ARK!")

    def __init__(self, line):
        self.player_name, self.event_type = self._get_player_info(line)
        super().__init__(line)

    def _get_player_info(self, line):
        match = self.regexp_pattern.search(line)
        if match:
            return match.group(1), match.group(2)
        return None, None

    def _post_classification(self):
        if self.event_type == "joined":
            if "send_welcome_message" in CONFIG and CONFIG["send_welcome_message"]:
                send_message_to_player(
                    self.player_name,
                    f'Welcome {self.player_name}! {CONFIG["tasks"]["announcement"]["description"]}',
                )
        elif self.event_type == "left":
            pass
        else:
            return
        count = get_active_players()
        player_str = f"({count} player{'s' if count != 1 else ''} {'online' if self.event_type == 'joined' else 'remaining'})"
        send_to_discord(
            f"{self.player_name} has {self.event_type} the server {player_str}",
            "log_webhook",
        )

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


class PlayerDied(LogEvent):
    EventInfo = namedtuple(
        "EventInfo", "tribe_name player_name level dinosaur dinosaur_level"
    )
    player_died_pattern = re.compile(
        r"Tribe\s+(.+?),\s+ID\s+\d+:\s+Day\s+\d+,\s+\d+:\d+:\d+:\s+<RichColor.+?>Tribemember\s+(.+?)\s+-\s+Lvl\s+(\d+)\s+was\s+killed(?:\s+by\s+a\s+(.+?)\s+-\s+Lvl\s+(\d+))?!"
    )

    @classmethod
    def is_event(cls, line: str):
        return "was killed" in line.lower() and "tribemember" in line.lower()

    def __init__(self, line: str):
        match = self.player_died_pattern.search(line)
        if match:
            self.event_info = self.EventInfo(*match.groups())
        else:
            self.event_info = self.EventInfo(None, None, None, None, None)
        super().__init__(line)

    def _post_classification(self):
        if self.event_info.player_name:
            message = f"{self.event_info.player_name} (Level {self.event_info.level}) of Tribe {self.event_info.tribe_name} was killed"
            if self.event_info.dinosaur:
                message += f" by {self.event_info.dinosaur} (Level {self.event_info.dinosaur_level})"
            send_to_discord(message, "log_webhook")

    def __str__(self):
        return f"PlayerDied Event: {self.message}"


class DinoTamed(LogEvent):
    EventInfo = namedtuple("EventInfo", "player_name tribe_name dinosaur level")
    dino_tamed_pattern = re.compile(
        r"(?:(?P<player_name>\w+) of )?Tribe (?P<tribe_name>[\w\s]*?) Tamed a(?:n)? (?P<dinosaur>.+?) - Lvl (?P<level>\d+)"
    )

    @classmethod
    def is_event(cls, line: str):
        return "tamed a" in line.lower() and "richcolor" not in line.lower()

    def __init__(self, line: str):
        self.message = self._get_message(line)
        # logger.info(f"Searching for {self.dino_tamed_pattern} in {self.message}")
        match = self.dino_tamed_pattern.search(self.message)
        if match:
            self.event_info = self.EventInfo(*match.groups())
        else:
            self.event_info = self.EventInfo(None, None, None, None)
        super().__init__(line)

    def _post_classification(self):
        if (
            self.event_info.player_name or self.event_info.tribe_name
        ) and self.event_info.dinosaur:
            message = f"{self.event_info.player_name or 'A player'} of Tribe {self.event_info.tribe_name or 'Unknown'} tamed a {self.event_info.dinosaur} (Level {self.event_info.level})"
            send_to_discord(message, "log_webhook")

    def __str__(self):
        return f"DinoTamed Event: {self.message}"


class GlobalChatMessage(LogEvent):
    EventInfo = namedtuple("EventInfo", "account_name player_name message")
    global_chat_pattern = re.compile(
        r"(?P<account_name>.+?)\s+\((?P<player_name>.+?)\):\s+(?P<message>.*?)$"
    )
    _last_match = None

    @classmethod
    def is_event(cls, line: str):
        # Perform the search and store the result
        message = cls._get_message(line)
        cls._last_match = cls.global_chat_pattern.search(message)
        return cls._last_match is not None

    def __init__(self, line: str):
        # Use the match stored in _last_match
        if self._last_match:
            match = self._last_match
            # Clear the match after use to prevent stale information
            self.__class__._last_match = None
            self.event_info = self.EventInfo(
                match.group("account_name"),
                match.group("player_name"),
                match.group("message"),
            )
        else:
            self.event_info = self.EventInfo(None, None, None)
        super().__init__(line)

    def _post_classification(self):
        if self.event_info.player_name and self.event_info.message:
            # Formulate the message to be sent to Discord
            message = f"{self.event_info.account_name} ({self.event_info.player_name}): {self.event_info.message}"
            send_to_discord(message, "chat_webhook")

    def __str__(self):
        return f"GlobalChatMessage Event: {self.event_info.account_name} ({self.event_info.player_name}): {self.event_info.message}"


if CONFIG["discord"]["events"]["player_connect"]:
    LogEventFactory.register_event_type(PlayerJoined)
    LogEventFactory.register_event_type(PlayerLeft)
if CONFIG["discord"]["events"]["player_died"]:
    LogEventFactory.register_event_type(PlayerDied)
if CONFIG["discord"]["events"]["dino_tamed"]:
    LogEventFactory.register_event_type(DinoTamed)
if CONFIG["discord"]["events"]["global_chat"]:
    LogEventFactory.register_event_type(GlobalChatMessage)


class LogMonitor:
    def __init__(self):
        self.filepath = os.path.join(
            CONFIG["server"]["install_path"],
            "ShooterGame",
            "Saved",
            "Logs",
            "ShooterGame.log",
        )
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
            with open(self.filepath, "r", encoding="utf-8") as file:
                file.seek(self.last_size)
                new_entries = file.readlines()
                self.last_size = current_size
        except FileNotFoundError:
            logger.error(f"Log file does not exist: {self.filepath}")
            # Handle file disappearance mid-operation if needed
        except OSError as e:
            logger.error(f"Error reading log file: {e}")
        except UnicodeDecodeError as e:
            logger.error(f"Error decoding log file: {e}")

        log_events = [LogEventFactory.create(line) for line in new_entries]
        return log_events


if __name__ == "__main__":
    test_strings = [
        "[2023.11.21-21.07.55:731][258]2023.11.21_21.07.55: Tribe Brohalla Tamed an Anglerfish - Lvl 224 (Anglerfish)!"
    ]

    for test_string in test_strings:
        event = LogEventFactory.create(test_string)
        print(f"Test string: {test_string}")
        print(f"Identified as: {event}")
        print("---------------------------------")
