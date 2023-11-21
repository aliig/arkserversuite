import threading
import time

from config import DEFAULT_CONFIG
from ini_parser import update_ark_configs
from log_monitor import LogMonitor
from logger import get_logger
from rcon import save_world, send_message
from shell_operations import (
    generate_batch_file,
    is_server_running,
    kill_server,
    run_shell_cmd,
)
from steamcmd import update_server
from tasks import (
    CheckForArkUpdatesAndRestart,
    CheckForModUpdatesAndRestart,
    DestroyWildDinos,
    HandleEmptyServerRestart,
    PerformRoutineRestart,
    SendAnnouncement,
    Task,
)
from update import does_server_need_update, is_server_installed
from utils import wait_until

logger = get_logger(__name__)


class ArkServerStartError(Exception):
    pass


class ArkServerStopError(Exception):
    pass


class ArkServer:
    def __init__(self):
        self.tasks: dict[str, Task] = self.initialize_tasks()
        self.running = True
        self.server_timeout = DEFAULT_CONFIG["advanced"].get("server_timeout", 300)
        self.sleep_time = DEFAULT_CONFIG["advanced"].get("sleep_time", 60)
        self.log_check_rate = DEFAULT_CONFIG["advanced"].get("log_check_rate", 5)

    def initialize_tasks(self):
        tasks_init = {
            "announcement": SendAnnouncement,
            "destroy_wild_dinos": DestroyWildDinos,
            "update": CheckForArkUpdatesAndRestart,
            "mod_update": CheckForModUpdatesAndRestart,
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
                is_server_running,
                lambda x: x,
                timeout=self.server_timeout,
                sleep_interval=3,
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
                timeout=self.server_timeout,
                sleep_interval=3,
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
            time.sleep(self.log_check_rate)

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
            time.sleep(self.sleep_time)

        log_monitor_thread.join()


if __name__ == "__main__":
    server = ArkServer()
    try:
        server.run()
    except KeyboardInterrupt:
        server._exit()
