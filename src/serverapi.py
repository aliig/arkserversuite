import os
import zipfile
import shutil

import requests

from config import CONFIG, OUTDIR
from utils import download_file
from logger import get_logger
from shell_operations import run_shell_cmd

logger = get_logger(__name__)

OWNER = "ServersHub"
REPO = "ServerAPI"
LOCAL_VERSION_FILE = os.path.join(OUTDIR, f"{OWNER}_{REPO}_timestamp.txt")
API_OUTDIR = os.path.join(
    CONFIG["server"]["install_path"], "ShooterGame", "Binaries", "Win64"
)
API_LOG_OUTDIR = os.path.join(API_OUTDIR, "logs")


def _extract_zip_and_move(zip_path: str, outdir: str):
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        for file in zip_ref.namelist():
            # Construct the full path to where the file should be extracted
            destination = os.path.join(outdir, file)

            # Check if the file or directory should be skipped
            if (file == "config.json" and os.path.exists(destination)) or (
                file.startswith("Plugins/")
                and os.path.exists(os.path.join(outdir, "Plugins"))
            ):
                logger.debug(f"Skipping {file} as it already exists.")
                continue

            # Extract and move the file
            source = zip_ref.extract(file, outdir)
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            shutil.move(source, destination)

    logger.debug(f"Extracted and moved files from {zip_path} to {outdir}")


def _get_latest_release_info(owner: str, repo: str) -> dict:
    api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    response = requests.get(api_url)
    if response.status_code == 200:
        release_data = response.json()
        return release_data["assets"][0]  # Assuming you want the first asset
    else:
        # logger.error("Failed to get the latest release from GitHub.")
        raise RuntimeError(
            f"Failed to get the latest {owner}/{repo} release from GitHub."
        )


def _download_latest_github_release(
    owner: str, repo: str, local_version_file: str
) -> str | None:
    asset = _get_latest_release_info(owner, repo)
    download_url = asset["browser_download_url"]
    zip_path = download_file(download_url, return_content=False)
    if zip_path:
        with open(local_version_file, "w") as file:
            file.write(asset["updated_at"])
        return zip_path
    else:
        logger.error(f"Failed to download {download_url}")
        return None


def _needs_update(latest_release_info: dict, local_version_file: str) -> bool:
    latest_timestamp = latest_release_info["updated_at"]
    if os.path.exists(local_version_file):
        with open(local_version_file, "r") as file:
            local_timestamp = file.read().strip()
        return latest_release_info if local_timestamp != latest_timestamp else False
    else:
        logger.debug(f"Local version file {local_version_file} does not exist.")
    return latest_release_info


def is_server_api_running() -> bool:
    process_name = "AsaApiLoader.exe"
    cmd = f'tasklist /FI "IMAGENAME eq {process_name}"'
    process = run_shell_cmd(cmd, suppress_output=True)
    return process.returncode == 0 and process_name in process.stdout


def is_server_api_ready() -> bool:
    directory = API_LOG_OUTDIR
    # Ensure the directory exists
    if not os.path.exists(directory):
        return False

    # List all files in the directory
    files = [os.path.join(directory, file) for file in os.listdir(directory)]

    # Filter out directories, keep only files
    files = [file for file in files if os.path.isfile(file)]

    # Sort files by modification time in descending order
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

    # Check if there are any files
    if not files:
        return False

    # Read the most recent file
    with open(files[0], "r") as f:
        contents = f.read()

    # Check if the specific string is in the file
    return "InitGame was called" in contents


def use_serverapi() -> bool:
    return "use_server_api" in CONFIG["server"] and CONFIG["server"]["use_server_api"]


def serverapi_needs_update() -> bool:
    return _needs_update(
        latest_release_info=_get_latest_release_info(OWNER, REPO),
        local_version_file=LOCAL_VERSION_FILE,
    )


def install_serverapi() -> None:
    zip_path = _download_latest_github_release(OWNER, REPO, LOCAL_VERSION_FILE)
    _extract_zip_and_move(zip_path, API_OUTDIR)
    if zip_path:
        logger.info(f"Downloaded latest {OWNER}/{REPO} release to {API_OUTDIR}")
    else:
        logger.debug(
            f"Latest {OWNER}/{REPO} release is already downloaded or failed to download."
        )
