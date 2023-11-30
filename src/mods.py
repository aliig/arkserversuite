import json
import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from functools import cache

import requests
from dotenv import load_dotenv

from config import CONFIG
from logger import get_logger
from crypto_script import decrypt_data
from utils import resource_path

logger = get_logger(__name__)

load_dotenv()  # Load environment variables from .env file


@dataclass
class Mod:
    name: str
    installed_dt: datetime | None
    latest_dt: datetime | None


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
            logger.debug("CURSEFORGE_API_KEY decrypted successfully")
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
    return "", None


def _get_latest_mods_timestamps(mod_ids: list[int]) -> dict[int, tuple[str, datetime]]:
    try:
        date_format = "%Y-%m-%dT%H:%M"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-api-key": _get_api_key(),
        }
        payload = {"modIds": mod_ids, "filterPcOnly": True}

        r = requests.post(
            "https://api.curseforge.com/v1/mods", headers=headers, json=payload
        )
        r.raise_for_status()

        response_data = r.json()
        latest_timestamps = {}
        for mod in response_data["data"]:
            mod_id = int(mod["id"])
            mod_name = mod["name"]
            date_string = mod["dateReleased"]
            last_colon_pos = date_string.rfind(":")
            new_string = date_string[:last_colon_pos]
            timestamp = datetime.strptime(new_string, date_format)
            latest_timestamps[mod_id] = (mod_name, timestamp)
            logger.debug(f"{mod['name']} latest timestamp: {timestamp}")

        return latest_timestamps
    except Exception as e:
        logger.error(e)
        return {}


def get_all_mods() -> list[Mod]:
    mod_list = list(_get_installed_mods())
    latest_timestamp_data = _get_latest_mods_timestamps(mod_list)

    all_mods = []
    for mod_id in mod_list:
        installed_name, installed_timestamp = _get_installed_mod_timestamp(mod_id)
        _, latest_timestamp = latest_timestamp_data.get(mod_id, ("", None))

        all_mods.append(
            Mod(
                name=installed_name,
                installed_dt=installed_timestamp,
                latest_dt=latest_timestamp,
            )
        )

    return all_mods


def mods_needing_update() -> list[Mod]:
    mods_update_list = []
    for mod in get_all_mods():
        if mod.installed_dt and mod.latest_dt:
            if mod.installed_dt < mod.latest_dt:
                mods_update_list.append(mod)

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
    print(mods_needing_update())
