import os

import steam.client
from steam.client import SteamClient

from config import DEFAULT_CONFIG
from logger import get_logger

logger = get_logger(__name__)

client = SteamClient()


def _get_latest_build_id(steam_app_id: int = DEFAULT_CONFIG["steam_app_id"]) -> str:
    if client.anonymous_login():
        app_info = client.get_product_info(apps=[steam_app_id])
        if app_info:
            # Extract the public branch buildid
            public_branch_info = app_info["apps"][steam_app_id]["depots"]["branches"][
                "public"
            ]
            client.disconnect()
            return public_branch_info["buildid"]
    return None


def _get_installed_build_id(
    steam_app_id: int = DEFAULT_CONFIG["steam_app_id"],
) -> str | None:
    appmanifest_name = f"appmanifest_{steam_app_id}.acf"
    appmanifest_path = os.path.join(
        DEFAULT_CONFIG["server"]["install_path"], "steamapps", appmanifest_name
    )

    if not os.path.isfile(appmanifest_path):
        logger.error(
            f"The appmanifest file for app ID {steam_app_id} does not exist at {appmanifest_path}."
        )
        return None

    try:
        with open(appmanifest_path, "r") as acf_file:
            for line in acf_file:
                if '"buildid"' in line:
                    build_id = line.split('"')[-2]
                    return build_id
    except IOError as e:
        logger.error(f"Error reading from {appmanifest_path}: {e}")
        return None

    logger.error(f"Build ID not found in {appmanifest_path}.")
    return None


def is_server_installed() -> bool:
    logger.info("Checking if the Ark server is installed...")
    return _get_installed_build_id() is not None


def does_server_need_update() -> bool:
    logger.info("Checking if the Ark server needs to be updated...")

    latest_build_id = _get_latest_build_id()
    installed_build_id = _get_installed_build_id()

    if latest_build_id is None or installed_build_id is None:
        return False

    status = (
        f"installed build_id: {installed_build_id}, latest build_id: {latest_build_id}"
    )

    if latest_build_id == installed_build_id:
        logger.info(f"The Ark server is up to date, {status}")
        return False

    logger.info(f"The Ark server needs to be updated, {status}")
    return True
