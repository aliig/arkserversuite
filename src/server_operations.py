from utils import rcon_cmd, send_to_discord, time_as_string

from logger import get_logger

logger = get_logger(__name__)


def send_message(message: str, discord_msg: bool = True) -> str:
    if message == "":
        return None
    if discord_msg:
        send_to_discord(message)
    return rcon_cmd(f"serverchat {message}")


def save_world() -> bool:
    res = rcon_cmd("saveworld")
    if res == "World Saved":
        send_to_discord(f"World saved at {time_as_string()}")
    return res


def destroy_wild_dinos() -> bool:
    res = rcon_cmd("destroywilddinos")
    if res == "All Wild Dinos Destroyed":
        send_to_discord(f"Dinosaurs reset at {time_as_string()}")
    return res


def get_active_players() -> int:
    response = rcon_cmd("ListPlayers")

    # Check for the "No Players Connected" response
    if "No Players Connected" in response:
        logger.info(f"Found 0 active players")
        return 0

    # Split the response by lines and count them to get the number of players
    count = len(response.strip().split("\n"))
    logger.info(f"Found {count} active players")
    return count

def send_message_to_player(player_name: str, message: str):
    return rcon_cmd(f"cheat ServerChatToPlayer {player_name} {message}")