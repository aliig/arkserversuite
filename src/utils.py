import os
import sys
import time
from datetime import datetime
from typing import Callable, TypeVar
import zipfile
import shutil

import requests

from config import CONFIG
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
        and webhook_type in CONFIG["discord"]
        and CONFIG["discord"][webhook_type]
    ):
        data = {"content": content}
        response = requests.post(CONFIG["discord"][webhook_type], json=data)
        logger.info(f"Sent message to Discord: {content}")
        return response.status_code == 204
    return None


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def download_file(url, target_path=None, return_content=False):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Error downloading file: {e}")
        return None

    if return_content:
        return response.content

    if not target_path:
        file_name = url.split("/")[-1]
        target_path = os.path.join(os.environ["TEMP"], file_name)

    with open(target_path, "wb") as file:
        file.write(response.content)

    return target_path
