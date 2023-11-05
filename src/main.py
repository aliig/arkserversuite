import time
from config import DEFAULT_CONFIG
from shell_operations import (
    is_server_running,
    generate_batch_file,
    run_shell_cmd,
    update_server,
)
from update import does_server_need_update
from utils import wait_until
from server_operations import (
    save_world,
    send_message,
)

from tasks import (
    CheckServerRunningAndRestart,
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
        # Time-related initializations
        self.reset_state()

        self.tasks: list[Task] = [
            CheckServerRunningAndRestart(self, time.time()),
            SendAnnouncement(self, time.time()),
            HandleEmptyServerRestart(self, time.time()),
            CheckForUpdatesAndRestart(self, time.time()),
            PerformRoutineRestart(self, time.time()),
            DestroyWildDinos(self, time.time()),
        ]

    def reset_state(self) -> None:
        current_time = time.time()
        self.last = {
            task_name: current_time for task_name in DEFAULT_CONFIG["tasks"].keys()
        }
        self.first_empty_server_time = None

    def start(self) -> bool:
        if not is_server_running():
            self.reset_state()
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
            run_shell_cmd("taskkill /IM ArkAscendedServer.exe /F", suppress_output=True)
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
            time.sleep(5)
            self.stop()
            time.sleep(5)
        self.start()

    def run(self) -> None:
        self.start()

        while True:
            for task in self.tasks:
                if task.execute(self, time.time()):
                    break
            time.sleep(60)  # Check every minute


if __name__ == "__main__":
    server = ArkServer()
    server.run()
