import os
import subprocess
import sys

from config import DEFAULT_CONFIG
from constants import OUTPUT_DIRECTORY
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


def get_process_id(expected_port: int) -> int | None:
    cmd = "netstat -ano"
    process = run_shell_cmd(cmd, suppress_output=True)

    if process.returncode != 0:
        print("Error running netstat:", process.stderr)
        return None

    for line in process.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1].startswith("0.0.0.0:"):
            port = int(parts[1].split(":")[1])
            if port == expected_port:
                process_id = int(parts[-1])
                logger.debug(f"Found process id {process_id} on port {port}")
                return process_id
    logger.debug(f"Process id on port {expected_port} not found")
    return None


def is_server_running(ark_port: int = DEFAULT_CONFIG["server"]["port"]) -> bool:
    if not (pid := get_process_id(ark_port)):
        return False

    try:
        cmd_str = f'tasklist /FI "PID eq {pid}"'
        result = run_shell_cmd(cmd_str, suppress_output=True)
        return pid in result.stdout
    except Exception as e:
        logger.error(f"Error checking if server is running: {e}")
        return False


def generate_batch_file() -> str:
    base_arg = os.path.join(
        DEFAULT_CONFIG["server"]["install_path"],
        "ShooterGame",
        "Binaries",
        "Win64",
        "ArkAscendedServer.exe",
    )
    question_mark_options = "?".join(
        [
            DEFAULT_CONFIG["server"]["map"],
            f"SessionName=\"{DEFAULT_CONFIG['server']['name']}\"",
            f"Port={DEFAULT_CONFIG['server']['port']}",
            f"QueryPort={DEFAULT_CONFIG['server']['query_port']}",
            f"Password={DEFAULT_CONFIG['server']['password']}",
            f"MaxPlayers={DEFAULT_CONFIG['server']['max_players']}",
            f"ServerAdminPassword={DEFAULT_CONFIG['server']['admin_password']}",
            "RCONEnabled=True",
            *DEFAULT_CONFIG["launch_options"]["question_mark"],
        ]
    )
    hyphen_options = " ".join(
        [f"-{opt}" for opt in DEFAULT_CONFIG["launch_options"].get("hyphen", []) if opt]
        + [
            f"-mods={','.join(map(str, DEFAULT_CONFIG['launch_options'].get('mods', [])))}"
            if DEFAULT_CONFIG["launch_options"].get("mods")
            else ""
        ]
        + [f"-WinLiveMaxPlayers={DEFAULT_CONFIG['server']['max_players']}"]
    )

    cmd_string = f"{base_arg} {question_mark_options} {hyphen_options}"
    batch_content = f'@echo off\nstart "" {cmd_string}'

    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    with open(
        (file_path := os.path.join(OUTPUT_DIRECTORY, ".start_server.bat")), "w"
    ) as batch_file:
        batch_file.write(batch_content)

    return file_path
