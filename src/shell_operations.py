import subprocess
import sys

from config import DEFAULT_CONFIG
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


def kill_server() -> None:
    run_shell_cmd("taskkill /IM ArkAscendedServer.exe /F", suppress_output=True)
    run_shell_cmd("taskkill /IM ShooterGameServer.exe /F", suppress_output=True)


def is_server_running() -> bool:
    try:
        cmd_str = 'tasklist /FI "IMAGENAME eq ArkAscendedServer.exe"'
        result = run_shell_cmd(cmd_str, suppress_output=True)
        return "ArkAscendedServer.exe" in result.stdout
    except Exception as e:
        logger.error(f"Error checking if server is running: {e}")
        return False


def generate_batch_file() -> str:
    base_arg = f"{DEFAULT_CONFIG['server']['install_path']}\\ShooterGame\\Binaries\\Win64\\ArkAscendedServer.exe"
    question_mark_options = "?".join(
        [
            DEFAULT_CONFIG["server"]["map"],
            f"SessionName=\"{DEFAULT_CONFIG['server']['name']}\"",
            f"Port={DEFAULT_CONFIG['server']['port']}",
            f"QueryPort={DEFAULT_CONFIG['server']['query_port']}",
            f"Password={DEFAULT_CONFIG['server']['password']}",
            f"MaxPlayers={DEFAULT_CONFIG['server']['players']}",
            f"ServerAdminPassword={DEFAULT_CONFIG['server']['admin_password']}",
            "RCONEnabled=True",
            *DEFAULT_CONFIG["launch_options"]["question_mark"],
        ]
    )
    hyphen_options = " ".join(
        [
            *map(lambda opt: f"-{opt}", DEFAULT_CONFIG["launch_options"]["hyphen"]),
            f"-mods={','.join(map(str, DEFAULT_CONFIG['launch_options']['mods']))}",
            f"-WinLiveMaxPlayers={DEFAULT_CONFIG['server']['players']}",
        ]
    )

    cmd_string = f"{base_arg} {question_mark_options} {hyphen_options}"
    batch_content = f'@echo off\nstart "" {cmd_string}'

    with open(".start_server.bat", "w") as batch_file:
        batch_file.write(batch_content)

    return ".start_server.bat"


def update_server() -> None:
    logger.info("Updating the Ark server...")
    cmd_str = (
        f"steamcmd.exe +force_install_dir {DEFAULT_CONFIG['server']['install_path']} +login "
        f"anonymous +app_update {DEFAULT_CONFIG['steam_app_id']} validate +quit"
    )
    run_shell_cmd(cmd_str)
