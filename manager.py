import subprocess
import time
import datetime
import yaml
import logging
import os
import sys
import threading

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


def run_with_timeout(func, condition, timeout):
    result_container = [None]

    def target():
        result_container[0] = func()

    thread = threading.Thread(target=target)

    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        return False
    return condition(result_container[0])


class ArkServer:
    def __init__(self, config_path: str = "config.yml"):
        # Load the configuration
        with open(config_path, "r") as stream:
            self.config = yaml.safe_load(stream)

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

    @staticmethod
    def _execute(
        cmd: str, suppress_output: bool = False
    ) -> subprocess.CompletedProcess:
        process = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True
        )

        # Print stdout and stderr to the console
        if not suppress_output:
            if process.stdout:
                print(process.stdout)
            if process.stderr:
                print(process.stderr, file=sys.stderr)

        return process

    def rcon_cmd(self, command: str) -> str:
        logging.info(f"Executing RCON command: {command}")
        cmd_str = f"{self.config['rcon']['path']}//rcon.exe -a {self.config['server']['ip_address']}:{self.config['rcon']['port']} -p {self.config['server']['password']} \"{command}\""
        return self._execute(cmd_str, suppress_output=True).stdout

    def wait_for_warnings(self, reason: str = "routine maintenance") -> None:
        warning_times = sorted(
            list(map(int, self.config["restart"]["warnings"])), reverse=True
        )
        anticipated_restart_time = (
            datetime.datetime.now() + datetime.timedelta(minutes=warning_times[0])
        ).strftime("%H:%M %p")

        for i, warning_time in enumerate(warning_times):
            self.send_message(
                f"Server will restart in {warning_time} minutes, at approximately {anticipated_restart_time}, for {reason}. Please prepare to log off."
            )
            if i < len(warning_times) - 1:
                time.sleep((warning_time - warning_times[i + 1]) * 60)
            else:
                time.sleep(warning_time * 60)

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

    def get_shortest_interval(self) -> float:
        smallest_warning = min(self.config["restart"]["warnings"]) * 60
        update_interval = self.config["restart"]["update_check"]["interval"] * 60 * 60
        announcement_interval = self.config["announcement"]["interval"] * 60 * 60

        return min(smallest_warning, update_interval, announcement_interval)

    def save_world(self) -> bool:
        logging.info("Saving world data...")
        res = self.rcon_cmd("saveworld")
        if "World Saved" in res:
            logging.info("World saved successfully!")
            return True
        logging.error("Failed to save the world. Please check for issues.")
        return False

    def count_active_players(self) -> int:
        response = self.rcon_cmd("ListPlayers")

        # Check for the "No Players Connected" response
        if "No Players Connected" in response:
            return 0

        # Split the response by lines and count them to get the number of players
        players = response.strip().split("\n")

        return len(players)

    def send_message(self, message: str) -> str:
        logging.info(f"Sending server message: {message}")
        return self.rcon_cmd(f"serverchat {message}")

    def is_running(self) -> bool:
        try:
            cmd_str = 'tasklist /FI "IMAGENAME eq ArkAscendedServer.exe"'
            result = self._execute(cmd_str, suppress_output=True)
            return "ArkAscendedServer.exe" in result.stdout
        except Exception as e:
            logging.error(f"Error checking if server is running: {e}")
            return False

    def _generate_batch_file(self):
        cmd_string = self._generate_server_args()
        batch_content = f'@echo off\nstart "" {cmd_string}'

        with open(".start_server.bat", "w") as batch_file:
            batch_file.write(batch_content)

        return ".start_server.bat"

    def start(self) -> bool:
        if not self.is_running():
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

    def _generate_server_args(self):
        """Generates the command-line arguments for starting the Ark server."""
        base_arg = f"{self.config['server']['install_path']}\\ShooterGame\\Binaries\\Win64\\ArkAscendedServer.exe"

        options = "?".join(
            [
                self.config["server"]["map"],
                f"SessionName=\"{self.config['server']['name']}\"",
                f"Port={self.config['server']['port']}",
                f"QueryPort={self.config['server']['query_port']}",
                f"Password={self.config['server']['password']}",
                f"MaxPlayers={self.config['server']['players']}",
                f"WinLiveMaxPlayers={self.config['server']['players']}",
                "AllowCrateSpawnsOnTopOfStructures=True",
                "RCONEnabled=True",
            ]
        )

        spaced_options = " ".join(
            [
                "-EnableIdlePlayerKick",
                "-NoBattlEye",
                "-servergamelog",
                "-servergamelogincludetribelogs",
                "-ServerRCONOutputTribeLogs",
                "-nosteamclient",
                "-game",
                "-server",
                "-log",
                f"-mods={','.join(map(str, self.config['mods']))}",
            ]
        )

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

    def needs_update(self) -> bool:
        logging.info("Checking for Ark server updates...")
        self.last_update_check = time.time()
        cmd_str = f"{self.config['steamcmd']['path']}\\steamcmd.exe +login {self.config['steamcmd']['username']} +app_info_print {self.config['steamcmd']['app_id']} +quit"
        result = self._execute(cmd_str)
        res = '"state" "eStateUpdateRequired"' in result.stdout
        if res:
            logging.info("Update available")
        self.update_queued = res
        return res

    def update(self) -> None:
        logging.info("Updating the Ark server...")
        cmd_str = (
            f"{self.config['steamcmd']['path']} +force_install_dir {self.config['server']['install_path']} +login "
            f"{self.config['steamcmd']['username']} +app_update {self.config['steamcmd']['app_id']} +quit"
        )
        self._execute(cmd_str)
        self.update_queued = False

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
