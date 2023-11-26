from config import DEFAULT_CONFIG
import os

# validate config


# check for steamcmd
STEAMCMD_DIR = os.path.join(
    DEFAULT_CONFIG["advanced"].get("output_directory", "output"), "steamcmd"
)
STEAMCMD_PATH = os.path.join(STEAMCMD_DIR, "steamcmd.exe")


def is_steam_cmd_installed():
    return os.path.isfile(STEAMCMD_PATH)


# check for directx
# check for ark server
