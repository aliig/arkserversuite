import subprocess
import time

import yaml


class ArkServer:
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the ArkServer instance.

        :param config_path: Path to the YAML configuration file.
        """
        with open(config_path, "r") as stream:
            self.config = yaml.safe_load(stream)
        self.server_process = None
        self.last_restart_time = time.time()

    def _execute(self, cmd_list: list[str]) -> subprocess.CompletedProcess:
        """
        Utility method to execute a subprocess command.

        :param cmd_list: The list of command arguments.
        :return: subprocess.CompletedProcess object.
        """
        return subprocess.run(cmd_list, capture_output=True, text=True)

    def _broadcast_restart_warnings(
        self, elapsed_time: float, RESTART_INTERVAL: float
    ) -> None:
        """
        Broadcast warnings to the server before an upcoming restart.

        :param elapsed_time: Time elapsed since the last restart.
        :param RESTART_INTERVAL: Configured interval for server restart.
        """
        for warning in self.config["intervals"]["warnings"]:
            if (
                RESTART_INTERVAL - elapsed_time
                <= warning["time"] * 60
                < RESTART_INTERVAL
                - elapsed_time
                + self.config["intervals"]["update_check"] * 60
            ):
                minutes_left = int(warning["time"])
                reason = "an update" if self.needs_update() else "regular maintenance"
                message = f"Server will restart in {minutes_left} minute{'s' if minutes_left > 1 else ''} due to {reason}."
                self.send_message(message)

    def rcon_cmd(self, command: str) -> str:
        """
        Run a command via RCON.

        :param command: The command to run.
        :return: STDOUT of the executed command.
        """
        base_cmd = [
            self.config["rcon"]["path"],
            "-a",
            f"{self.config['server']['ip_address']}:{self.config['rcon']['port']}",
            "-p",
            self.config["server"]["password"],
        ]
        return self._execute(base_cmd + command.split()).stdout

    def send_message(self, message: str) -> None:
        """
        Send a server chat message.

        :param message: The message to send.
        """
        self.rcon_cmd(f"serverchat {message}")

    def is_running(self) -> bool:
        """
        Check if the Ark server is running.

        :return: True if running, False otherwise.
        """
        result = self._execute(
            ["tasklist", "/FI", "IMAGENAME eq ArkAscendedServer.exe"]
        )
        return "ArkAscendedServer.exe" in result.stdout

    def start(self) -> None:
        """Start the Ark server."""
        if not self.is_running():
            args = self._generate_server_args()
            self.server_process = subprocess.Popen(args)
            self.last_restart_time = time.time()

    def _generate_server_args(self) -> list[str]:
        """
        Generates the command-line arguments for starting the Ark server.

        :return: List of command-line arguments.
        """
        base_args = [
            f"{self.config['server']['binary_path']}\\ArkAscendedServer.exe",
            "TheIsland_WP",
        ]
        options = [
            # Extracting server options for clarity
            f"?Port={self.config['server']['port']}",
            # ... (rest of the options) ...
        ]
        return base_args + options

    def stop(self) -> None:
        """Stop the Ark server."""
        if self.is_running():
            self.send_message("Saving world data...")
            subprocess.run(["taskkill", "/IM", "ArkAscendedServer.exe", "/F"])

    def needs_update(self) -> bool:
        """
        Check if the Ark server needs an update.

        :return: True if update is required, False otherwise.
        """
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
        """Update the Ark server."""
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

    def run(self) -> None:
        """
        The main loop for managing the Ark server. It checks for required updates,
        sends warnings for upcoming restarts, and ensures that the server is running.
        """
        RESTART_INTERVAL = self.config["intervals"]["restart"] * 60 * 60
        UPDATE_CHECK_INTERVAL = self.config["intervals"]["update_check"] * 60 * 60

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

            for warning in self.config["intervals"]["warnings"]:
                if elapsed_time >= RESTART_INTERVAL - warning["time"] * 60:
                    message = f"Server will restart in {warning['time']} minute(s)."
                    self.send_message(message)

            if elapsed_time >= RESTART_INTERVAL or update_detected:
                # Close the server
                print("Closing the Ark server...")
                self.stop()

                # If it's an update, update the server
                if update_detected:
                    print("Update available. Updating the server...")
                    self.update_ark()

                # Restart server
                print("Restarting the Ark server...")
                self.start()
                self.last_restart_time = time.time()

            time.sleep(UPDATE_CHECK_INTERVAL)

    def _handle_restart(self, update_detected: bool) -> None:
        """
        Handle the server restart logic.

        :param update_detected: True if an update was detected, False otherwise.
        """
        self.stop()
        if update_detected:
            print("Update available. Updating the server...")
            self.update()
        print("Restarting the Ark server...")
        self.start()


if __name__ == "__main__":
    server = ArkServer()
    server.run()
