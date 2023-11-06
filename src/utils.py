import socket
import struct
import requests
from datetime import datetime
import time
from typing import Callable, TypeVar

from config import DEFAULT_CONFIG

from logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


def time_as_string(time: datetime = None) -> str:
    # desire "%H:%M %p" format
    if time is None:
        time = datetime.now()
    return time.strftime("%H:%M %p")


def wait_until(
    func: Callable[[], T],
    is_success: Callable[[T], bool],
    timeout: float,
    sleep_interval: float = 0.05,
) -> tuple[T, bool]:
    start = time.time()
    while (time.time() - start) < timeout:
        res = func()
        if is_success(res):
            return res, True
        time.sleep(sleep_interval)
    return res, False


def send_to_discord(content: str) -> bool:
    """Sends a message to Discord via a webhook."""
    data = {"content": content}
    response = requests.post(DEFAULT_CONFIG["discord"]["webhook"], json=data)
    logger.info(f"Sent message to Discord: {content}")
    return response.status_code == 204


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


def rcon_cmd(command) -> str | None:
    try:
        args = (
            DEFAULT_CONFIG["server"]["ip_address"],
            DEFAULT_CONFIG["server"]["rcon_port"],
            DEFAULT_CONFIG["server"]["admin_password"],
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
