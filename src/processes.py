import psutil

from logger import get_logger
from config import CONFIG

logger = get_logger(__name__)


def kill_server() -> None:
    """
    Kills the server processes.
    """
    for process in psutil.process_iter(["pid", "name"]):
        if process.info["name"] in ["ArkAscendedServer.exe", "AsaApiLoader.exe"]:
            process.terminate()
            logger.debug(
                f"Terminated process {process.info['name']} with PID {process.info['pid']}"
            )


def get_process_from_port(expected_port: int) -> int | None:
    """
    Retrieves the process ID that is using the specified port.

    :param expected_port: The port number to check.
    :return: The process ID if found, otherwise None.
    """
    for conn in psutil.net_connections(kind="inet"):
        if conn.laddr.port == expected_port:
            res = conn.pid
            logger.debug(f"Process id on port {expected_port} found: {res}")
            return res
    logger.debug(f"Process id on port {expected_port} not found")
    return None


def is_server_running(ark_port: int = CONFIG["server"]["port"]) -> bool:
    """
    Checks if the server is running on the specified port.

    :param ark_port: The port number to check.
    :return: True if the server is running, False otherwise.
    """
    pid = get_process_from_port(ark_port)
    if pid is None:
        return False
    try:
        return psutil.pid_exists(pid)
    except Exception as e:
        logger.error(f"Error checking if server is running: {e}")
        return False


def get_parent_from_child(child_pid: int) -> int | None:
    """
    Retrieves the parent process ID of a given child process ID.

    :param child_pid: The process ID of the child process.
    :return: The process ID of the parent process, or None if not found.
    """
    try:
        child_process = psutil.Process(child_pid)
        parent_process = child_process.parent()
        if parent_process is None:
            logger.debug(f"No parent process found for child PID {child_pid}")
            return None
        return parent_process.pid
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        logger.error(f"Error retrieving parent process for PID {child_pid}")
        return None
