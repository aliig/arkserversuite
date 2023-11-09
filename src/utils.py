import os
import socket
import struct
import time
import urllib.request
from datetime import datetime
from typing import Callable, TypeVar

import requests

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


def _send_to_discord(content: str, webhook_type: str = "updates_webhook") -> bool:
    data = {"content": content}
    response = requests.post(DEFAULT_CONFIG["discord"][webhook_type], json=data)
    logger.info(f"Sent message to Discord: {content}")
    return response.status_code == 204


def send_to_discord(content: str, webhook_type: str = "updates_webhook") -> bool | None:
    """Sends a message to Discord via a webhook."""
    if (
        content
        and webhook_type in DEFAULT_CONFIG["discord"]
        and DEFAULT_CONFIG["discord"][webhook_type]
    ):
        return _send_to_discord(content, webhook_type)
    return None


def check_and_download_steamcmd(working_directory):
    # Path to steamcmd.exe in the working directory
    steamcmd_path = os.path.join(working_directory, "steamcmd.exe")

    # URL to download steamcmd.exe
    steamcmd_url = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip"

    # Check if steamcmd.exe exists
    if not os.path.isfile(steamcmd_path):
        print("steamcmd.exe not found, downloading...")
        # Download steamcmd.zip
        zip_path = os.path.join(working_directory, "steamcmd.zip")
        urllib.request.urlretrieve(steamcmd_url, zip_path)
        print("Downloaded steamcmd.zip")

        # Here you would normally extract the zip file and clean up
        # For example, using zipfile module to extract and os.remove to delete the zip file
        # This part of the code is left as an exercise

        print("steamcmd.exe is ready to use.")
    else:
        print("steamcmd.exe is already present.")
