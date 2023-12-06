import socket
import struct

from config import CONFIG
from logger import get_logger
from utils import send_to_discord, time_as_string

logger = get_logger(__name__)


class RCON:
    SERVERDATA_EXECCOMMAND = 2
    SERVERDATA_AUTH = 3

    def __init__(self, host, port, password):
        self.host = host
        self.port = port
        self.password = password
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.req_id = 1

    def _send(self, out_type, command):
        data = (
            struct.pack("<ii", self.req_id, out_type)
            + command.encode("utf-8")
            + b"\x00\x00"
        )
        self.sock.send(struct.pack("<i", len(data)) + data)

        (length,) = struct.unpack("<i", self.sock.recv(4))
        resp = self.sock.recv(length)

        if len(resp) < 8:
            raise Exception(f"Unexpected RCON response: {resp}")

        (
            resp_id,
            resp_type,
        ) = struct.unpack("<ii", resp[:8])

        if resp_id == -1:
            raise Exception("RCON authentication failed.")
        return resp[8:-2].decode("utf-8")

    def connect(self):
        self.sock.connect((self.host, self.port))
        self._send(self.SERVERDATA_AUTH, self.password)

    def send(self, command):
        return self._send(self.SERVERDATA_EXECCOMMAND, command)

    def close(self):
        self.sock.close()


def _rcon_cmd(command) -> str | None:
    try:
        args = (
            CONFIG["server"]["ip_address"],
            CONFIG["server"]["rcon_port"],
            CONFIG["server"]["admin_password"],
        )
        logger.info(f"Sending RCON command: {command}")
        rcon = RCON(*args)
        rcon.connect()
        response = rcon.send(command)
        return response
    except Exception as e:
        # Logging or raising an exception might be better than print
        logger.error(f"RCON with args {args} and command {command} failed: {e}")
        return None
    finally:
        rcon.close()


from logger import get_logger

logger = get_logger(__name__)


def send_message(message: str, discord_msg: bool = True) -> str:
    if message == "":
        return None
    if discord_msg:
        send_to_discord(message)
    return _rcon_cmd(f"serverchat {message}")


def broadcast(message: str, discord_msg: bool = True) -> str:
    if message == "":
        return None
    if discord_msg:
        send_to_discord(message)
    return _rcon_cmd(f"broadcast {message}")


def save_world() -> bool:
    res = _rcon_cmd("saveworld")
    if res == "World Saved":
        send_to_discord(f"World saved at {time_as_string()}")
    return res


def destroy_wild_dinos() -> bool:
    res = _rcon_cmd("destroywilddinos")
    if res == "All Wild Dinos Destroyed":
        send_to_discord(f"Dinosaurs reset at {time_as_string()}")
    return res


def get_active_players() -> int:
    response = _rcon_cmd("ListPlayers")
    if not response:
        logger.error(f"Error getting active players")
        return None

    # Check for the "No Players Connected" response
    if "No Players Connected" in response:
        logger.info(f"Found 0 active players")
        return 0

    # Split the response by lines and count them to get the number of players
    count = len(response.strip().split("\n"))
    logger.info(f"Found {count} active players")
    return count


def send_message_to_player(player_name: str, message: str):
    return _rcon_cmd(f"ServerChatToPlayer {player_name} {message}")
