import json
import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from functools import cache

import requests
from dotenv import load_dotenv

from config import CONFIG, OUTDIR
from crypto_script import decrypt_data
from logger import get_logger
from utils import resource_path

logger = get_logger(__name__)

load_dotenv()  # Load environment variables from .env file


@dataclass
class Mod:
    name: str
    installed_dt: datetime | None
    latest_dt: datetime | None
    is_approved: bool = False


@cache
def _decrypt_api_key() -> str:
    try:
        encrypted_key_path = resource_path("encrypted_key.enc")
        passphrase_path = resource_path("passphrase.txt")

        with open(encrypted_key_path, "rb") as file:
            encrypted_data_with_salt = file.read()
        with open(passphrase_path, "r") as file:
            passphrase = file.read().strip()

        return decrypt_data(encrypted_data_with_salt, passphrase).decode()
    except Exception as e:
        logger.error(f"Error decrypting CURSEFORGE_API_KEY: {e}")
        return None


def _get_api_key() -> str:
    if key := os.getenv("CURSEFORGE_API_KEY"):
        logger.debug("CURSEFORGE_API_KEY found in environment variables")
    else:
        # get key from file with decryption
        if key := _decrypt_api_key():
            logger.debug(f"CURSEFORGE_API_KEY of length {len(key)} decrypted")
        else:
            logger.warning("CURSEFORGE_API_KEY failed to decrypt or returned None")
    return key


@cache
def _local_mod_file() -> dict:
    file_path = os.path.join(
        CONFIG["server"]["install_path"],
        "ShooterGame/Binaries/Win64/ShooterGame/ModsUserData/83374/library.json",
    )
    # load file as json into python dict
    with open(file_path, encoding="utf-8-sig") as f:  # Specify UTF-8 encoding
        data = json.load(f)

    return data


def _get_installed_mods() -> set[int]:
    mods = set()
    for i in _local_mod_file()["installedMods"]:
        mods.add(int(i["installedFile"]["modId"]))
    return mods


def _get_installed_mod_timestamp(mod_id: int) -> tuple[str, datetime | None]:
    date_format = "%Y.%m.%d-%H.%M"
    local_mod_data = _local_mod_file()

    try:
        for mod in local_mod_data["installedMods"]:
            if int(mod["installedFile"]["modId"]) == mod_id:
                mod_name = mod["details"]["name"]
                date_string = mod["installedFile"]["fileDate"]
                last_period_pos = date_string.rfind(".")
                new_string = date_string[:last_period_pos]

                timestamp = datetime.strptime(new_string, date_format)
                logger.debug(f"{mod_name} installed timestamp: {timestamp}")

                return mod_name, timestamp
    except Exception as e:
        logger.error(e)
        # pretty print the local_mod_data as json
        print(json.dumps(local_mod_data, indent=4))
    return "", None


def _fetch_mod_data(mod_ids: int | list[int]) -> dict:
    """
    Fetches mod data from the CurseForge API based on the provided mod IDs.

    :param mod_ids: A single mod ID or a list of mod IDs to query.
    :return: A dictionary containing the response data from the API.
    """
    try:
        # Convert a single integer to a list
        if isinstance(mod_ids, int):
            mod_ids = [mod_ids]

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-api-key": _get_api_key(),
        }
        payload = {"modIds": mod_ids, "filterPcOnly": True}
        response = requests.post(
            "https://api.curseforge.com/v1/mods", headers=headers, json=payload
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(e)
        return {}


def _get_remote_mod_info(
    mod_ids: list[int],
) -> dict[int, tuple[str, datetime, bool]]:
    """
    Fetches the latest info for mods based on provided mod IDs.

    :param mod_ids: A list of mod IDs to query.
    :return: A dictionary mapping mod IDs to a tuple of mod name, latest timestamp, and approval status.
    """
    try:
        date_format = "%Y-%m-%dT%H:%M"
        response_data = _fetch_mod_data(mod_ids)
        if CONFIG["advanced"]["log_level"] == "debug":
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            outdir = os.path.join(OUTDIR, "mods")
            os.makedirs(outdir, exist_ok=True)
            filepath = os.path.join(outdir, f"{timestamp}_mods.json")
            with open(filepath, "w") as f:
                json.dump(response_data, f, indent=4)

        latest_timestamps = {}
        for mod in response_data.get("data", []):
            mod_id = int(mod["id"])
            mod_name = mod["name"]
            date_string = mod["dateReleased"]
            last_colon_pos = date_string.rfind(":")
            new_string = date_string[:last_colon_pos]
            timestamp = datetime.strptime(new_string, date_format)
            is_approved = (
                mod["latestFiles"]["isAvailable"] == True
                and int(mod["latestFiles"]["fileStatus"]) == 4
            )
            latest_timestamps[mod_id] = (mod_name, timestamp, is_approved)
            logger.debug(f"{mod_name} latest timestamp: {timestamp}")

        return latest_timestamps
    except Exception as e:
        logger.error(e)
        print("Response data:")
        print(json.dumps(response_data, indent=4))
        return {}


def get_all_mods() -> list[Mod]:
    mod_list = list(_get_installed_mods())
    remote_mod_info = _get_remote_mod_info(mod_list)

    all_mods = []
    for mod_id in mod_list:
        installed_name, installed_timestamp = _get_installed_mod_timestamp(mod_id)
        _, latest_timestamp, is_approved = remote_mod_info.get(
            mod_id, ("", None, False)
        )

        all_mods.append(
            Mod(
                name=installed_name,
                installed_dt=installed_timestamp,
                latest_dt=latest_timestamp,
                is_approved=is_approved,
            )
        )

    return all_mods


def mods_needing_update() -> list[Mod]:
    mods_update_list = []
    time_diff = CONFIG["advanced"].get("mod_update_timestamp_threshold", 60)
    for mod in get_all_mods():
        if mod.installed_dt and mod.latest_dt:
            if abs((mod.latest_dt - mod.installed_dt).total_seconds()) > time_diff * 60:
                if mod.is_approved:
                    mods_update_list.append(mod)
                else:
                    logger.info(
                        f"{mod.name} has a newer version that is not yet approved or available, skipping update"
                    )

    return mods_update_list


def delete_mods_folder() -> None:
    mods_folder = os.path.join(
        CONFIG["server"]["install_path"],
        "ShooterGame/Binaries/Win64/ShooterGame/Mods",
    )
    mods_user_data_folder = os.path.join(
        CONFIG["server"]["install_path"],
        "ShooterGame/Binaries/Win64/ShooterGame/ModsUserData",
    )

    try:
        shutil.rmtree(mods_folder)
        logger.debug(f"Deleted mods folder: {mods_folder}")
        shutil.rmtree(mods_user_data_folder)
        logger.debug(f"Deleted mods user data folder: {mods_user_data_folder}")
    except FileNotFoundError:
        logger.warning("Mods folder not found, skipping deletion")
    except Exception as e:
        logger.error(f"An error occurred: {e}")


if __name__ == "__main__":
    try:
        mods_update_list = mods_needing_update()
        print(mods_update_list)
    except Exception as e:
        logger.error(e)

    mod_data = _fetch_mod_data(927090)

    # Write mod data to JSON file
    output_dir = os.path.join(os.getcwd(), "output")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "mod_data.json")

    with open(output_file, "w") as f:
        json.dump(mod_data, f, indent=4)  # Pretty print with indent=4
