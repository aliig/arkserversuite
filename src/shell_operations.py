import subprocess
from config import DEFAULT_CONFIG
import sys
import re

from logger import get_logger

logger = get_logger(__name__)


def run_shell_cmd(
    cmd: str,
    suppress_output: bool = False,
    use_popen: bool = False,
    use_shell: bool = True,
) -> subprocess.CompletedProcess:
    kwargs = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
        "shell": use_shell,
    }

    if use_popen:
        process = subprocess.Popen(cmd, **kwargs)
    else:
        process = subprocess.run(cmd, **kwargs)

    # Print stdout and stderr to the console
    if not suppress_output:
        if process.stdout:
            print(process.stdout)
        if process.stderr:
            print(process.stderr, file=sys.stderr)

    return process


def is_server_running() -> bool:
    try:
        cmd_str = 'tasklist /FI "IMAGENAME eq ArkAscendedServer.exe"'
        result = run_shell_cmd(cmd_str, suppress_output=True)
        return "ArkAscendedServer.exe" in result.stdout
    except Exception as e:
        print(f"Error checking if server is running: {e}")
        return False


def generate_batch_file() -> str:
    base_arg = f"{DEFAULT_CONFIG['server']['install_path']}\\ShooterGame\\Binaries\\Win64\\ArkAscendedServer.exe"
    options = "?".join(
        [
            DEFAULT_CONFIG["server"]["map"],
            f"SessionName=\"{DEFAULT_CONFIG['server']['name']}\"",
            f"Port={DEFAULT_CONFIG['server']['port']}",
            f"QueryPort={DEFAULT_CONFIG['server']['query_port']}",
            f"Password={DEFAULT_CONFIG['server']['password']}",
            f"MaxPlayers={DEFAULT_CONFIG['server']['players']}",
            f"WinLiveMaxPlayers={DEFAULT_CONFIG['server']['players']}",
            "AllowCrateSpawnsOnTopOfStructures=True",
            "RCONEnabled=True",
        ]
    )
    spaced_options = " ".join(
        [
            "-EnableIdlePlayerKick",
            "-NoBattlEye",
            "-servergamelog",
            "-servergamelogincludetribelogs",
            "-ServerRCONOutputTribeLogs",
            "-nosteamclient",
            "-game",
            "-server",
            "-log",
            f"-mods={','.join(map(str, DEFAULT_CONFIG['mods']))}",
        ]
    )

    cmd_string = f"{base_arg} {options} {spaced_options}"
    batch_content = f'@echo off\nstart "" {cmd_string}'

    with open(".start_server.bat", "w") as batch_file:
        batch_file.write(batch_content)

    return ".start_server.bat"


def _get_latest_build_id(app_info_output: str) -> str:
    # This function should extract the latest build ID for the public branch from the steamcmd output
    latest_build_match = re.search(
        r'"public"\s*{\s*"buildid"\s*"(\d+)"', app_info_output
    )
    if latest_build_match:
        return latest_build_match.group(1)
    return None


def _get_installed_build_id(app_status_output: str) -> str:
    # This function should extract the installed build ID from the steamcmd output
    installed_build_match = re.search(r"BuildID (\d+)", app_status_output)
    if installed_build_match:
        return installed_build_match.group(1)
    return None


def does_server_need_update() -> bool:
    logger.info("Checking if the Ark server needs to be updated...")

    # First, run the command to get the installed build ID
    app_status_cmd = f"{DEFAULT_CONFIG['steamcmd']['path']}\\steamcmd.exe +force_install_dir {DEFAULT_CONFIG['server']['install_path']} +login anonymous +app_status {DEFAULT_CONFIG['steamcmd']['app_id']} +quit"
    app_status_result = run_shell_cmd(app_status_cmd, suppress_output=True)
    installed_build_id = _get_installed_build_id(app_status_result.stdout)

    # Next, run the command to get the latest build ID
    attempts = 0
    while attempts <= 5:
        app_info_cmd = f"{DEFAULT_CONFIG['steamcmd']['path']}\\steamcmd.exe +force_install_dir {DEFAULT_CONFIG['server']['install_path']} +login anonymous +app_info_update 1 +app_info_print {DEFAULT_CONFIG['steamcmd']['app_id']} +quit"
        app_info_result = run_shell_cmd(app_info_cmd, suppress_output=True)
        latest_build_id = _get_latest_build_id(app_info_result.stdout)
        # sometimes doesn't return anything? not sure why...
        if latest_build_id is not None:
            break
        attempts += 1

    if installed_build_id and latest_build_id and installed_build_id != latest_build_id:
        logger.info(
            f"Update needed: Installed build ID ({installed_build_id}) does not match latest build ID ({latest_build_id})."
        )
        return True

    logger.info(
        f"No update needed. Latest build ID ({latest_build_id}) matches installed build ID ({installed_build_id})."
    )
    return False


def update_server() -> None:
    logger.info("Updating the Ark server...")
    cmd_str = (
        f"{DEFAULT_CONFIG['steamcmd']['path']}\\steamcmd.exe +force_install_dir {DEFAULT_CONFIG['server']['install_path']} +login "
        f"anonymous +app_update {DEFAULT_CONFIG['steamcmd']['app_id']} +quit"
    )
    run_shell_cmd(cmd_str)
