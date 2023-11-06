import time
from config import DEFAULT_CONFIG
from shell_operations import (
    is_server_running,
    generate_batch_file,
    run_shell_cmd,
    kill_server,
    update_server,
)
from update import does_server_need_update
from utils import wait_until
from server_operations import (
    save_world,
    send_message,
)

from tasks import (
    SendAnnouncement,
    HandleEmptyServerRestart,
    CheckForUpdatesAndRestart,
    PerformRoutineRestart,
    DestroyWildDinos,
    Task,
)

from logger import get_logger

logger = get_logger(__name__)

SLEEP_TIME = 60  # seconds to sleep between server state checks


class ArkServerStartError(Exception):
    pass


class ArkServerStopError(Exception):
    pass


class ArkServer:
    def __init__(self):
        self.tasks: dict[str, Task] = self.initialize_tasks()

    def initialize_tasks(self):
        tasks_init = {
            "announcement": SendAnnouncement,
            "stale": HandleEmptyServerRestart,
            "update": CheckForUpdatesAndRestart,
            "restart": PerformRoutineRestart,
            "destroy_wild_dinos": DestroyWildDinos,
        }

        tasks = {}
        for task_name, task_class in tasks_init.items():
            logger.info(f"Initializing task: {task_name}")
            tasks[task_name] = task_class(self, task_name)

        return tasks

    def start(self) -> bool:
        if not is_server_running():
            if does_server_need_update():
                update_server()

            batch_file_path = generate_batch_file()
            cmd = ["cmd", "/c", batch_file_path]
            logger.info(f"Starting Ark server with cmd: {cmd}")
            run_shell_cmd(cmd, use_shell=False, use_popen=True, suppress_output=True)

            _, success = wait_until(
                is_server_running, lambda x: x, timeout=20, sleep_interval=1
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
                is_server_running, lambda x: not x, timeout=20, sleep_interval=1
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
            self.tasks["restart"].time.reset_next_time()
            time.sleep(5)
            self.stop()
            time.sleep(5)
        self.start()

    def run(self) -> None:
        self.start()
        while True:
            if not is_server_running():
                logger.info("Server is not running. Attempting to restart...")
                self.start()

            for _, task in self.tasks.items():
                if task.execute():
                    break
            time.sleep(SLEEP_TIME)  # Check every minute


if __name__ == "__main__":
    server = ArkServer()
    server.run()
