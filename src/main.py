import time

from constants import INI_INIT_TIMEOUT, SERVER_TIMEOUT, SLEEP_TIME, LOG_CHECK_RATE
from ini_parser import ini_file, update_ark_configs
from log_monitor import LogMonitor
from logger import get_logger
from rcon import save_world, send_message
from shell_operations import (
    generate_batch_file,
    is_server_running,
    kill_server,
    run_shell_cmd,
    get_process_id,
)
from steamcmd import update_server
from tasks import (
    CheckForUpdatesAndRestart,
    DestroyWildDinos,
    HandleEmptyServerRestart,
    PerformRoutineRestart,
    SendAnnouncement,
    Task,
)
from update import does_server_need_update, is_server_installed
from utils import wait_until
import threading

logger = get_logger(__name__)


class ArkServerStartError(Exception):
    pass


class ArkServerStopError(Exception):
    pass


class ArkServer:
    def __init__(self):
        self.tasks: dict[str, Task] = self.initialize_tasks()
        self.running = True

    def initialize_tasks(self):
        tasks_init = {
            "announcement": SendAnnouncement,
            "destroy_wild_dinos": DestroyWildDinos,
            "update": CheckForUpdatesAndRestart,
            "restart": PerformRoutineRestart,
            "stale": HandleEmptyServerRestart,
        }

        tasks = {}
        for task_name, task_class in tasks_init.items():
            logger.debug(f"Initializing task: {task_name}")
            tasks[task_name] = task_class(self, task_name)

        return tasks

    def start(self) -> bool:
        if not is_server_running():
            if does_server_need_update():
                update_server()

            batch_file_path = generate_batch_file()
            cmd = ["cmd", "/c", batch_file_path]
            logger.debug(f"Starting Ark server with cmd: {cmd}")
            run_shell_cmd(cmd, use_shell=False, use_popen=True, suppress_output=True)

            _, success = wait_until(
                is_server_running, lambda x: x, timeout=SERVER_TIMEOUT, sleep_interval=1
            )
            if not success:
                logger.error("Failed to start the Ark server")
                raise ArkServerStartError("Failed to start the Ark server.")
            else:
                logger.info("Ark server started")
            return success
        else:
            logger.info("Ark server is already running")
        return True

    def stop(self) -> bool:
        if is_server_running():
            logger.info("Stopping the Ark server...")
            save_world()
            time.sleep(5)
            kill_server()
            _, success = wait_until(
                is_server_running,
                lambda x: not x,
                timeout=SERVER_TIMEOUT,
                sleep_interval=1,
            )
            if success:
                logger.info("Ark server stopped")
            else:
                logger.error("Failed to stop the Ark server")
                raise ArkServerStopError("Failed to stop the Ark server.")
            return success
        else:
            logger.info("Ark server is not running")
        return True

    def restart(self, reason: str = "other") -> None:
        if is_server_running():
            send_message(f"Server is restarting for {reason}.")
            self.tasks["restart"].time.reset()
            self.tasks["update"].time.reset()
            time.sleep(5)
            self.stop()
            time.sleep(5)
        self.start()

    def _pre_run(self) -> None:
        if not is_server_installed():
            update_server("Installing the Ark server...")
            logger.info("Ark server installed")
        update_ark_configs()

    def _run_log_monitor(self):
        log_monitor = LogMonitor()
        while self.running:
            log_monitor.process_new_entries()
            time.sleep(LOG_CHECK_RATE)

    def _exit(self) -> None:
        logger.info("Exiting...")
        self.running = False

    def run(self) -> None:
        self._pre_run()
        self.start()

        log_monitor_thread = threading.Thread(target=self._run_log_monitor)
        log_monitor_thread.start()

        while self.running:
            if not is_server_running():
                logger.info("Server is not running. Attempting to restart...")
                self.start()

            for _, task in self.tasks.items():
                if task.execute():
                    break
            time.sleep(SLEEP_TIME)

        log_monitor_thread.join()


if __name__ == "__main__":
    server = ArkServer()
    try:
        server.run()
    except KeyboardInterrupt:
        server._exit()
