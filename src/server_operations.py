from utils import rcon_cmd, send_to_discord, time_as_string
from config import DEFAULT_CONFIG


import datetime
import time

from logger import get_logger
logger = get_logger(__name__)


def send_message(message: str, discord_msg: bool = True) -> str:
    if discord_msg:
        send_to_discord(message)
    return rcon_cmd(f"serverchat {message}")


def save_world() -> bool:
    res = rcon_cmd("saveworld")
    if res == "World Saved":
        send_to_discord(f"World saved at {time_as_string()}")
    return res


def get_active_players() -> int:
    response = rcon_cmd("ListPlayers")

    # Check for the "No Players Connected" response
    if "No Players Connected" in response:
        return 0

    # Split the response by lines and count them to get the number of players
    count = len(response.strip().split("\n"))
    logger.info(f"Found {count} active players")
    return len(count)


def warn_and_wait(reason: str = "unknown") -> None:
    warning_times = sorted(
        list(map(int, DEFAULT_CONFIG["restart"]["warnings"])), reverse=True
    )
    anticipated_restart_time = (
        datetime.datetime.now() + datetime.timedelta(minutes=warning_times[0])
    ).strftime("%H:%M %p")

    for i, warning_time in enumerate(warning_times):
        send_message(
            f"Server will restart in {warning_time} minutes, at approximately {anticipated_restart_time}, for {reason}. Please prepare to log off."
        )
        if i < len(warning_times) - 1:
            time.sleep((warning_time - warning_times[i + 1]) * 60)
        else:
            time.sleep(warning_time * 60)
