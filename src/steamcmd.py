import os
import urllib.request
import zipfile

from config import CONFIG
from logger import get_logger
from shell_operations import run_shell_cmd

logger = get_logger(__name__)


STEAMCMD_DIR = os.path.join(
    CONFIG["advanced"].get("output_directory", "output"), "steamcmd"
)
STEAMCMD_PATH = os.path.join(STEAMCMD_DIR, "steamcmd.exe")


def _run_steamcmd(args: str) -> None:
    logger.debug(f"Run steamcmd.exe with {STEAMCMD_PATH} {args}")
    run_shell_cmd(f"{STEAMCMD_PATH} {args}")


def is_steam_cmd_installed():
    return os.path.isfile(STEAMCMD_PATH)


def check_and_download_steamcmd():
    if not is_steam_cmd_installed():
        logger.info("steamcmd.exe not found, downloading...")
        zip_path = os.path.join(
            CONFIG["advanced"].get("output_directory", "output"), "steamcmd.zip"
        )
        try:
            urllib.request.urlretrieve(
                CONFIG["advanced"]["download_url"]["steamcmd"],
                zip_path,
            )
            logger.debug("Downloaded steamcmd.zip")

            # Create the steamcmd directory if it doesn't exist
            os.makedirs(STEAMCMD_DIR, exist_ok=True)

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                # Extract directly into the steamcmd directory
                zip_ref.extractall(STEAMCMD_DIR)
            logger.debug("Extracted steamcmd.exe")

            # Remove the downloaded zip file
            os.remove(zip_path)
            logger.debug("Removed steamcmd.zip")

        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise e


def update_server(msg: str = "Updating the Ark server...") -> None:
    logger.info(msg)
    check_and_download_steamcmd()
    args = f"+force_install_dir {os.path.join(CONFIG['server']['install_path'])} +login anonymous +app_update {CONFIG['steam_app_id']} validate +quit"
    _run_steamcmd(args)


if __name__ == "__main__":
    check_and_download_steamcmd()
