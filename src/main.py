import time
import datetime
from config import DEFAULT_CONFIG
from shell_operations import is_server_running, does_server_need_update, generate_batch_file, run_shell_cmd, update_server
from utils import wait_until
from server_operations import save_world, send_message, get_active_players, warn_and_wait

from logger import get_logger
logger = get_logger(__name__)

SLEEP_TIME = 60 #seconds to sleep between server state checks
FIRST_ANNOUNCEMENT_TIME = 120 #seconds to wait to send first server announcement

class ArkServerStartError(Exception):
    pass

class ArkServerStopError(Exception):
    pass

class ArkServer:
    def __init__(self):
        # Time-related initializations
        self.reset_state()

        # Intervals and thresholds setup from config
        self.restart_interval = (
            DEFAULT_CONFIG["restart"]["scheduled"]["interval"] * 60 * 60
        )
        self.update_check_interval = (
            DEFAULT_CONFIG["restart"]["update_check"]["interval"] * 60 * 60
        )
        self.announcement_interval = DEFAULT_CONFIG["announcement"]["interval"] * 60 * 60
        self.stale_check_interval = DEFAULT_CONFIG["stale"]["interval"] * 60 * 60
        self.stale_restart_threshold = DEFAULT_CONFIG["stale"]["threshold"] * 60 * 60

        # Announcement and update flags/settings
        self.routine_announcement_message = DEFAULT_CONFIG["announcement"]["message"]
        self.update_queued = False

    def reset_state(self) -> None:
        # Time-related initializations
        self.last_restart_time = time.time()
        self.last_announcement_time = time.time()
        self.last_update_check = time.time()
        self.last_stale_check = time.time()
        self.first_empty_server_time = None
        self.welcome_message_sent = False

    def is_blackout_time(self) -> bool:
        blackout_start, blackout_end = DEFAULT_CONFIG["restart"]["scheduled"][
            "blackout_times"
        ]
        h_start, m_start = map(int, blackout_start.split(":"))
        h_end, m_end = map(int, blackout_end.split(":"))

        current_time = datetime.datetime.now()
        blackout_start_time = datetime.time(h_start, m_start)
        blackout_end_time = datetime.time(h_end, m_end)

        if blackout_start_time > blackout_end_time:  # The time wraps to the next day
            return (
                current_time >= blackout_start_time or current_time <= blackout_end_time
            )
        else:
            return blackout_start_time <= current_time <= blackout_end_time

    def start(self) -> bool:
        self.reset_state()
        if not is_server_running():
            if does_server_need_update():
                update_server()

            batch_file_path = generate_batch_file()
            cmd = ["cmd", "/c", batch_file_path]
            logger.info(f"Starting Ark server with cmd: {cmd}")
            run_shell_cmd(cmd, use_shell=False, use_popen=True, suppress_output=True)

            _, success = wait_until(is_server_running, lambda x: x, timeout=20, sleep_interval=1)
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
            _, success = wait_until(is_server_running, lambda x: not x, timeout=20, sleep_interval=1)
            if success:
                logger.info("Ark server stopped")
            else:
                logger.error("Failed to stop the Ark server")
                raise ArkServerStopError("Failed to stop the Ark server.")
            return success
        else:
            logger.info("Ark server is not running")
        return True

    def restart(
        self, reason: str = "other", skip_warnings: bool = False
    ) -> None:
        if not skip_warnings:
            warn_and_wait(reason)
        if is_server_running():
            send_message(f"Server is restarting for {reason}.")
            time.sleep(3)
            self.stop()
        self.start()

    def run(self) -> None:
        self.start()  # Start the server initially.

        while True:
            current_time = time.time()
            # If the server is not running, attempt to restart it
            if not is_server_running():
                logger.info("Server is not running. Attempting to restart...")
                self.restart(skip_warnings=True)
                continue

            # if first announcement needed on server start
            if (
                current_time - self.last_restart_time >= FIRST_ANNOUNCEMENT_TIME
                and not self.welcome_message_sent
            ):
                send_message(self.routine_announcement_message, discord_msg=False)
                self.welcome_message_sent = True

            # if routine periodic announcement needed
            if current_time - self.last_announcement_time >= self.announcement_interval:
                # Use the function to get the expected restart time
                send_message(self.routine_announcement_message, discord_msg=False)
                self.last_announcement_time = current_time

            # periodically restart an empty server
            if current_time - self.last_stale_check >= self.stale_check_interval:
                if get_active_players() == 0:
                    if self.first_empty_server_time == None:
                        logger.info("Server is empty, starting stale check timer...")
                        self.first_empty_server_time = current_time
                    else:
                        if (
                            current_time - self.first_empty_server_time
                            >= self.stale_restart_threshold
                        ):
                            logger.info("Server is stale, restarting...")
                            self.restart("stale server", skip_warnings=True)
                            continue
                else:
                    if self.first_empty_server_time is not None:
                        logger.info(
                            "Server is no longer empty, resetting stale check timer..."
                        )
                        self.first_empty_server_time = None
                self.last_stale_check = current_time

            # check for updates
            if current_time - self.last_update_check >= self.update_check_interval and does_server_need_update():
                self.restart("server update")
                continue

            # if routine restart needed
            if (
                current_time - self.last_restart_time >= self.restart_interval
            ) and not self.is_blackout_time():
                self.restart("routine restart")
                continue

            time.sleep(SLEEP_TIME)


if __name__ == "__main__":
    server = ArkServer()
    server.run()
