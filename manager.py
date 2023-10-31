import subprocess
import time
import datetime
import pytz
import yaml
import logging

# Setting up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


class ArkServer:
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, "r") as stream:
            self.config = yaml.safe_load(stream)
        self.server_process = None
        self.last_restart_time = time.time()
        self.announcement_message = self.config["announcement"]["message"]
        self.last_announcement_time = time.time()
        self.sent_warnings = set()

    def _execute(self, cmd_list: list[str]) -> subprocess.CompletedProcess:
        return subprocess.run(cmd_list, capture_output=True, text=True)

    def _broadcast_restart_warnings(
        self, elapsed_time: float, RESTART_INTERVAL: float
    ) -> None:
        for warning in self.config["restart"]["warnings"]:
            minutes_left = int(warning)
            if RESTART_INTERVAL - elapsed_time <= warning * 60:
                if minutes_left not in self.sent_warnings:
                    reason = (
                        "an update" if self.needs_update() else "regular maintenance"
                    )
                    message = f"Server will restart in {minutes_left} minute{'s' if minutes_left > 1 else ''} due to {reason}. Expected restart time: {self.get_next_restart_time_in_et()} ET."
                    self.send_message(message)
                    self.sent_warnings.add(minutes_left)

    def get_next_restart_time_in_et(self) -> str:
        local_time = datetime.datetime.now()
        seconds_until_next_restart = self.restart_interval - (
            time.time() - self.last_restart_time
        )
        next_restart_time_local = local_time + datetime.timedelta(
            seconds=seconds_until_next_restart
        )

        # Convert to Eastern Time
        local_time_zone = pytz.timezone(
            "UTC"
        )  # Assuming server is in UTC, change if different
        eastern_time_zone = pytz.timezone("US/Eastern")
        next_restart_time_et = next_restart_time_local.astimezone(
            local_time_zone
        ).astimezone(eastern_time_zone)

        return next_restart_time_et.strftime("%H:%M %p")

    def is_blackout_time(self) -> bool:
        blackout_start, blackout_end = self.config["restart"]["scheduled"][
            "blackout_times"
        ]
        h_start, m_start = map(int, blackout_start.split(":"))
        h_end, m_end = map(int, blackout_end.split(":"))

        current_time = (
            datetime.datetime.now().astimezone(pytz.timezone("US/Eastern")).time()
        )
        blackout_start_time = datetime.time(h_start, m_start)
        blackout_end_time = datetime.time(h_end, m_end)

        if blackout_start_time > blackout_end_time:  # The time wraps to the next day
            return (
                current_time >= blackout_start_time or current_time <= blackout_end_time
            )
        else:
            return blackout_start_time <= current_time <= blackout_end_time

    def get_shortest_interval(self) -> float:
        smallest_warning = (
            min(self.config["restart"]["warnings"]) * 60
        )  # Convert to seconds
        update_interval = self.config["restart"]["update_check"]["interval"] * 60 * 60
        announcement_interval = self.config["announcement"]["interval"] * 60 * 60

        return min(smallest_warning, update_interval, announcement_interval)

    def rcon_cmd(self, command: str) -> str:
        base_cmd = [
            self.config["rcon"]["path"],
            "-a",
            f"{self.config['server']['ip_address']}:{self.config['rcon']['port']}",
            "-p",
            self.config["server"]["password"],
        ]
        return self._execute(base_cmd + command.split()).stdout

    def send_message(self, message: str) -> None:
        self.rcon_cmd(f"serverchat {message}")

    def is_running(self) -> bool:
        result = self._execute(
            ["tasklist", "/FI", "IMAGENAME eq ArkAscendedServer.exe"]
        )
        return "ArkAscendedServer.exe" in result.stdout

    def start(self) -> None:
        if not self.is_running():
            args = self._generate_server_args()
            self.server_process = subprocess.Popen(args)
            self.last_restart_time = time.time()

    def _generate_server_args(self):
        """Generates the command-line arguments for starting the Ark server."""
        base_args = [
            f"{self.config['server']['binary_path']}\\ArkAscendedServer.exe",
            "TheIsland_WP",
        ]
        options = [
            f"?Port={self.config['server']['port']}",
            f"?QueryPort={self.config['server']['query_port']}",
            f"?MaxPlayers={self.config['server']['players']}",
            f"?Password={self.config['server']['password']}",
            "?AllowCrateSpawnsOnTopOfStructures=True",
            "?RCONEnabled=True",
            "-EnableIdlePlayerKick",
            "-NoBattlEye",
            "-servergamelog",
            "-servergamelogincludetribelogs",
            "-ServerRCONOutputTribeLogs",
            "-nosteamclient",
            "-game",
            "-server",
            "-log",
        ]
        return base_args + options

    def stop(self) -> None:
        if self.is_running():
            self.send_message("Saving world data...")
            subprocess.run(["taskkill", "/IM", "ArkAscendedServer.exe", "/F"])

    def needs_update(self) -> bool:
        result = self._execute(
            [
                self.config["steamcmd"]["path"],
                "+login",
                self.config["steamcmd"]["username"],
                "+app_info_print",
                str(self.config["steamcmd"]["app_id"]),
                "+quit",
            ]
        )
        return '"state" "eStateUpdateRequired"' in result.stdout

    def update(self) -> None:
        self._execute(
            [
                self.config["steamcmd"]["path"],
                "+force_install_dir",
                self.config["steamcmd"]["install_path"],
                "+login",
                self.config["steamcmd"]["username"],
                "+app_update",
                str(self.config["steamcmd"]["app_id"]),
                "+quit",
            ]
        )

    def restart_server(self, reason="scheduled restart"):
        """Handle the server restart process."""
        logging.info(f"Closing the Ark server for {reason}...")
        self.stop()

        logging.info(f"Restarting the Ark server...")
        self.start()
        self.last_restart_time = time.time()
        self.sent_warnings.clear()  # Reset sent warnings

    def run(self) -> None:
        RESTART_INTERVAL = self.config["restart"]["scheduled"]["interval"] * 60 * 60
        UPDATE_CHECK_INTERVAL = (
            self.config["restart"]["update_check"]["interval"] * 60 * 60
        )
        ANNOUNCEMENT_INTERVAL = self.config["announcement"]["interval"] * 60 * 60
        SLEEP_INTERVAL = self.get_shortest_interval()

        self.start()  # Start the server initially.

        while True:
            # Check if the server is running
            if not self.is_running():
                print("Server is not running. Attempting to restart...")
                if not self.start():  # Try to start the server.
                    print("Failed to restart the server. Exiting...")
                    exit(1)  # Exit the program with an error code.

            elapsed_time = time.time() - self.last_restart_time
            update_detected = self.needs_update()

            if not self.is_blackout_time():
                self._broadcast_restart_warnings(elapsed_time, RESTART_INTERVAL)

            # Routine announcement check
            if time.time() - self.last_announcement_time >= ANNOUNCEMENT_INTERVAL:
                # Use the function to get the expected restart time
                self.send_message(self.announcement_message)
                self.last_announcement_time = time.time()

            # Routine restart check
            if elapsed_time >= RESTART_INTERVAL:
                if self.is_blackout_time():
                    print("Blackout time detected. Skipping scheduled restart.")
                else:
                    # Close the server
                    print("Closing the Ark server for scheduled restart...")
                    self.stop()

                    # Restart server
                    print("Restarting the Ark server...")
                    self.start()
                    self.last_restart_time = time.time()
                    self.sent_warnings.clear()  # Reset sent warnings

            # Update check
            elif update_detected:  # Handle updates separately
                # Close the server
                print("Update available. Closing the Ark server for update...")
                self.stop()

                # Update the server
                print("Updating the Ark server...")
                self.update()

                # Restart server
                print("Restarting the Ark server after update...")
                self.start()
                self.last_restart_time = time.time()

            time.sleep(SLEEP_INTERVAL)


if __name__ == "__main__":
    server = ArkServer()
    server.run()
