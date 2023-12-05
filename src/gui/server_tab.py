import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from typing import Dict


class ServerTab(ttk.Frame):
    """
    GUI component representing a single server tab.
    """

    def __init__(self, parent, server_config: Dict) -> None:
        """
        Initialize the server tab with specific server configuration.

        :param parent: The parent widget, typically a notebook tab.
        :param server_config: Configuration details for the server.
        """
        super().__init__(parent)
        self.server_config = server_config

        # Example layout
        self.setup_ui()

    def setup_ui(self) -> None:
        """
        Sets up the user interface components for the server tab.
        """
        # Example label showing server information - customize as needed
        self.server_info_label = ttk.Label(
            self, text=f"Server Info: {self.server_config.get('info', 'N/A')}"
        )
        self.server_info_label.pack(pady=10)

        # Example button for server actions - customize as needed
        self.restart_button = ttk.Button(
            self, text="Restart Server", command=self.restart_server, bootstyle=PRIMARY
        )
        self.restart_button.pack(pady=10)

    def restart_server(self):
        """
        Example method to restart the server.
        """
        # Implement server restart logic
        print("Restarting server...")
