import os
import sys
import time
from datetime import datetime
from typing import Callable, TypeVar

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
