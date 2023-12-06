import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from .scrollable_frame import ScrollableFrame


class SettingsTab(ScrollableFrame):
    """
    GUI component representing the settings tab within a server panel.
    """

    def __init__(self, parent) -> None:
        """
        Initialize the settings tab with specific server configuration.

        :param parent: The parent widget, typically a notebook tab.
        :param server_config: Configuration details for the server.
        """
        super().__init__(parent)
        self.server_config = {}

        self.setup_ui()

    def setup_ui(self) -> None:
        """
        Sets up the user interface components for the settings tab.
        """
        # Create and place your settings widgets inside self.inner_frame

        # Example section for basic server settings
        self.basic_settings_frame = ttk.LabelFrame(
            self.inner_frame, text="Basic Settings", padding=10
        )
        self.basic_settings_frame.pack(fill="both", expand=True, pady=10)

        # Example entry for server name
        ttk.Label(self.basic_settings_frame, text="Server Name:").pack(side="left")
        self.server_name_entry = ttk.Entry(
            self.basic_settings_frame,
            textvariable=ttk.StringVar(value=self.server_config.get("name", "")),
        )
        self.server_name_entry.pack(side="right", fill="x", expand=True)

        # More settings can be added here, such as IP address, port, etc.

        # Example section for advanced server settings
        self.advanced_settings_frame = ttk.LabelFrame(
            self.inner_frame, text="Advanced Settings", padding=10
        )
        self.advanced_settings_frame.pack(fill="both", expand=True, pady=10)

        # Add more advanced settings widgets here
        # For example, toggles for server features, performance settings, etc.
