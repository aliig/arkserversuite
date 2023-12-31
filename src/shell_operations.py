import os
import subprocess
import sys

from config import CONFIG, OUTDIR
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


def generate_batch_file() -> str:
    """
    Generates a batch file based on the provided configuration.
    :return: The path to the generated batch file.
    """

    def _server_config_option(key: str, format_str: str) -> str | None:
        """
        Formats a server configuration option.

        :param key: The key of the configuration option.
        :param format_str: The format string.
        :return: The formatted string or None if the key is not found.
        """
        value = CONFIG["server"].get(key)
        return format_str.format(value) if value else None

    def _construct_base_arg() -> str:
        """
        Constructs the base argument for the command string.

        :return: The base argument string.
        """
        exe_name = (
            "AsaApiLoader.exe"
            if CONFIG["server"].get("use_server_api")
            else "ArkAscendedServer.exe"
        )
        return os.path.join(
            CONFIG["server"]["install_path"],
            "ShooterGame",
            "Binaries",
            "Win64",
            exe_name,
        )

    def _construct_question_mark_options() -> str:
        """
        Constructs the question mark options for the command string.

        :return: The question mark options string.
        """
        options = [CONFIG["server"]["map"]]
        question_mark_options_list = [
            _server_config_option("ip_address", "MultiHome={}"),
            # _server_config_option('name', "SessionName=\"{}\""),
            _server_config_option("port", "Port={}"),
            _server_config_option("query_port", "QueryPort={}"),
            # _server_config_option("password", "Password={}"),
            _server_config_option("max_players", "MaxPlayers={}"),
            # _server_config_option("admin_password", "ServerAdminPassword={}"),
            "RCONEnabled=True",
        ]
        options.extend(filter(None, question_mark_options_list))

        question_mark_config_options = CONFIG["launch_options"].get("question_mark", [])
        if question_mark_config_options:
            options.extend(question_mark_config_options)
        return "?".join(filter(None, options))

    def _construct_hyphen_options() -> str:
        """
        Constructs the hyphen options for the command string.

        :return: The hyphen options string.
        """
        hyphen_options = CONFIG["launch_options"].get("hyphen", [])
        options = [f"-{opt}" for opt in hyphen_options if opt]
        mods = CONFIG["launch_options"].get("mods")
        if mods:
            options.append(f"-mods={','.join(map(str, mods))}")
        options.append(f"-WinLiveMaxPlayers={CONFIG['server']['max_players']}")
        return " ".join(options)

    base_arg = _construct_base_arg()
    question_mark_options = _construct_question_mark_options()
    hyphen_options = _construct_hyphen_options()

    cmd_string = f"{base_arg} {question_mark_options} {hyphen_options}"
    logger.debug(f"launch options: {cmd_string}")
    batch_content = f'@echo off\nstart "" {cmd_string}'

    file_path = os.path.join(OUTDIR, ".start_server.bat")
    with open(file_path, "w") as batch_file:
        batch_file.write(batch_content)

    return file_path
