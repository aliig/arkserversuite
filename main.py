import subprocess
import time
import datetime
import yaml
import logging
import os
import sys
import threading
import requests

from config import DEFAULT_CONFIG

# Setting up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
)


# Custom class to redirect stdout and stderr to logger
class LoggerToFile:
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level

    def write(self, message):
        # Eliminate extra newlines in logger output
        if message != "\n":
            self.logger.log(self.level, message)

    def flush(self):
        pass  # Leave it empty to satisfy the stream interface


sys.stdout = LoggerToFile(logging.getLogger(), logging.INFO)
sys.stderr = LoggerToFile(logging.getLogger(), logging.ERROR)


class ArkServer:
    def __init__(self):
        # Time-related initializations
        self.last_restart_time = time.time()
        self.last_announcement_time = time.time()
        self.last_update_check = time.time()
        self.last_stale_check = time.time()

        # Intervals and thresholds setup from config
        self.restart_interval = (
            self.config["restart"]["scheduled"]["interval"] * 60 * 60
        )
        self.update_check_interval = (
            self.config["restart"]["update_check"]["interval"] * 60 * 60
        )
        self.announcement_interval = self.config["announcement"]["interval"] * 60 * 60
        self.stale_check_interval = self.config["stale"]["interval"] * 60 * 60
        self.stale_restart_threshold = self.config["stale"]["threshold"] * 60 * 60

        # Announcement and update flags/settings
        self.routine_announcement_message = self.config["announcement"]["message"]
        self.update_queued = False
        self.first_empty_server_time = None

        # Determine shortest interval for sleep period
        self.sleep_interval = self.get_shortest_interval()

        self.welcome_message_sent = False
        self.discord_webhook = self.config["discord"]["webhook"]

    def get_shortest_interval(self) -> float:
        smallest_warning = min(self.config["restart"]["warnings"]) * 60
        update_interval = self.config["restart"]["update_check"]["interval"] * 60 * 60
        announcement_interval = self.config["announcement"]["interval"] * 60 * 60

        return min(smallest_warning, update_interval, announcement_interval)

    def is_blackout_time(self) -> bool:
        blackout_start, blackout_end = self.config["restart"]["scheduled"][
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

    def start() -> bool:
        if not is_server_running():
            if self.update_queued or self.needs_update():
                self.update()

            batch_file_path = self._generate_batch_file()
            cmd = ["cmd", "/c", batch_file_path]
            logging.info(f"Starting Ark server with cmd: {cmd}")
            subprocess.Popen(cmd, shell=True)
            self.last_restart_time = time.time()
            self.welcome_message_sent = False
            res = run_with_timeout(self.is_running, lambda x: x, 20)
            if not res:
                logging.error("Failed to start the Ark server")
                return False
            else:
                logging.info("Ark server started")
        else:
            logging.info("Ark server is already running")
        return True

        # Combining everything into one single string
        return f"{base_arg} {options} {spaced_options}"

    def stop(self) -> bool:
        if self.is_running():
            logging.info("Stopping the Ark server...")
            self.save_world()
            res = subprocess.run(["taskkill", "/IM", "ArkAscendedServer.exe", "/F"])
            if res.returncode == 0:
                logging.info("Ark server stopped")
            else:
                logging.error("Failed to stop the Ark server")
                return False
        else:
            logging.info("Ark server is not running")
        return True

    def restart_server(
        self, reason: str = "scheduled restart", skip_warnings: bool = False
    ) -> bool:
        if not skip_warnings:
            self.wait_for_warnings(reason)
        self.send_message(f"Server is restarting for {reason}.")
        self.stop()
        res = self.start()
        self.first_empty_server_time = None
        return res

    def run(self) -> None:
        self.start()  # Start the server initially.

        while True:
            # Check if the server is running
            if not self.is_running():
                print("Server is not running. Attempting to restart...")
                if not self.restart_server(
                    skip_warnings=True
                ):  # Try to start the server.
                    print("Failed to restart the server. Exiting...")
                    exit(1)  # Exit the program with an error code.

            # if first announcement needed on server start
            if (
                time.time() - self.last_restart_time >= 2 * 60
                and not self.welcome_message_sent
            ):
                self.send_message(self.routine_announcement_message)
                self.welcome_message_sent = True

            # if routine announcement needed
            if time.time() - self.last_announcement_time >= self.announcement_interval:
                # Use the function to get the expected restart time
                self.send_message(self.routine_announcement_message)
                self.last_announcement_time = time.time()

            # periodically restart an empty server
            if time.time() - self.last_stale_check >= self.stale_check_interval:
                if self.count_active_players() == 0:
                    if self.first_empty_server_time == None:
                        logging.info("Server is empty, starting stale check timer...")
                        self.first_empty_server_time = time.time()
                    else:
                        if (
                            time.time() - self.first_empty_server_time
                            >= self.stale_restart_threshold
                        ):
                            logging.info("Server is stale, restarting...")
                            self.restart_server("stale server", skip_warnings=True)
                else:
                    if self.first_empty_server_time is not None:
                        logging.info(
                            "Server is no longer empty, resetting stale check timer..."
                        )
                        self.first_empty_server_time = None
                self.last_stale_check = time.time()

            # check for updates
            if self.update_queued or (
                time.time() - self.last_update_check >= self.update_check_interval
                and self.needs_update()
            ):
                self.restart_server("server update")

            # if routine restart needed
            if (
                time.time() - self.last_restart_time >= self.restart_interval
            ) and not self.is_blackout_time():
                self.restart_server("routine restart")

            time.sleep(self.sleep_interval)


if __name__ == "__main__":
    server = ArkServer()
    server.run()
