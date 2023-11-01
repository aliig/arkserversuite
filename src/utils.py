import socket
import struct
import threading
import subprocess
import sys
import requests
import datetime

from config import DEFAULT_CONFIG


def time_as_string(time: datetime.datetime = None) -> str:
    # desire "%H:%M %p" format
    if time is None:
        time = datetime.datetime.now()
    return time.strftime("%H:%M %p")


def run_with_timeout(func, condition, timeout):
    result_container = [None]

    def target():
        result_container[0] = func()

    thread = threading.Thread(target=target)

    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        return False
    return condition(result_container[0])


def send_to_discord(content: str) -> bool:
    """Sends a message to Discord via a webhook."""
    data = {"content": content}
    response = requests.post(DEFAULT_CONFIG["discord"]["webhook"], json=data)
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


def rcon_cmd(command):
    rcon = RCON(
        DEFAULT_CONFIG["server"]["ip_address"],
        DEFAULT_CONFIG["rcon"]["port"],
        DEFAULT_CONFIG["server"]["password"],
    )
    rcon.connect()
    response = rcon.send(command)
    rcon.close()
    return response
