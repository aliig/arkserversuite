import os
import urllib.request
import zipfile

from config import DEFAULT_CONFIG
from constants import OUTPUT_DIRECTORY
from logger import get_logger
from shell_operations import run_shell_cmd

logger = get_logger(__name__)

STEAMCMD_DIR = os.path.join(OUTPUT_DIRECTORY, "steamcmd")
STEAMCMD_PATH = os.path.join(STEAMCMD_DIR, "steamcmd.exe")


def _run_steamcmd(args: str) -> None:
    run_shell_cmd(f"{STEAMCMD_PATH} {args}")


def _check_and_download_steamcmd():
    if not os.path.isfile(STEAMCMD_PATH):
        logger.info("steamcmd.exe not found, downloading...")
        zip_path = os.path.join(OUTPUT_DIRECTORY, "steamcmd.zip")
        try:
            urllib.request.urlretrieve(
                "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip",
                zip_path,
            )
            logger.info("Downloaded steamcmd.zip")

            # Create the steamcmd directory if it doesn't exist
            os.makedirs(STEAMCMD_DIR, exist_ok=True)

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                # Extract directly into the steamcmd directory
                zip_ref.extractall(STEAMCMD_DIR)
            logger.info("Extracted steamcmd.exe")

            # Remove the downloaded zip file
            os.remove(zip_path)
            logger.info("Removed steamcmd.zip")

        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise e


def update_server(msg: str = "Updating the Ark server...") -> None:
    logger.info(msg)
    _check_and_download_steamcmd()
    args = f"+force_install_dir {os.path.join(DEFAULT_CONFIG['server']['install_path'])} +login anonymous +app_update {DEFAULT_CONFIG['steam_app_id']} validate +quit"
    _run_steamcmd(args)


if __name__ == "__main__":
    _check_and_download_steamcmd()
