import os
import urllib.request
import zipfile

from config import DEFAULT_CONFIG
from logger import get_logger
from shell_operations import run_shell_cmd

logger = get_logger(__name__)


def _run_steamcmd(args: str) -> None:
    run_shell_cmd(f"steamcmd.exe {args}")


def _check_and_download_steamcmd():
    # Path to steamcmd.exe in the working directory
    steamcmd_path = "steamcmd.exe"

    # Check if steamcmd.exe exists
    if not os.path.isfile(steamcmd_path):
        logger.info("steamcmd.exe not found, downloading...")
        zip_path = "steamcmd.zip"
        try:
            urllib.request.urlretrieve(
                "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip",
                zip_path,
            )
            logger.info("Downloaded steamcmd.zip")
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall()
            logger.info("Extracted steamcmd.exe")
            os.remove(zip_path)
            logger.info("Removed steamcmd.zip")

        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise e


def update_server() -> None:
    logger.info("Updating the Ark server...")
    args = f"+force_install_dir {os.path.join(DEFAULT_CONFIG['server']['install_path'])} +login anonymous +app_update {DEFAULT_CONFIG['steam_app_id']} validate +quit"
    _check_and_download_steamcmd()
    _run_steamcmd(args)


if __name__ == "__main__":
    _check_and_download_steamcmd()
