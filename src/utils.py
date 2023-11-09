import os
import time
import urllib.request
import zipfile
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


def send_to_discord(content: str, webhook_type: str = "updates_webhook") -> bool | None:
    """Sends a message to Discord via a webhook."""
    if (
        content
        and webhook_type in DEFAULT_CONFIG["discord"]
        and DEFAULT_CONFIG["discord"][webhook_type]
    ):
        data = {"content": content}
        response = requests.post(DEFAULT_CONFIG["discord"][webhook_type], json=data)
        logger.info(f"Sent message to Discord: {content}")
        return response.status_code == 204
    return None


def check_and_download_steamcmd(working_directory: str = ""):
    # Path to steamcmd.exe in the working directory
    steamcmd_path = os.path.join(working_directory, "steamcmd.exe")

    # URL to download steamcmd.exe
    steamcmd_url = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip"

    # Check if steamcmd.exe exists
    if not os.path.isfile(steamcmd_path):
        logger.info("steamcmd.exe not found, downloading...")
        zip_path = os.path.join(working_directory, "steamcmd.zip")
        try:
            urllib.request.urlretrieve(steamcmd_url, zip_path)
            logger.info("Downloaded steamcmd.zip")
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(working_directory)
            logger.info("Extracted steamcmd.exe")
            os.remove(zip_path)
            logger.info("Removed steamcmd.zip")

        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise e


if __name__ == "__main__":
    check_and_download_steamcmd()
