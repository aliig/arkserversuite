import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from .server_tabs.commands import CommandsTab
from .server_tabs.mods import ModsTab
from .server_tabs.settings import SettingsTab
from .server_tabs.summary import SummaryTab


class ServerPanel(ttk.Frame):
    """
    GUI component representing the panel that contains all the server-specific tabs.
    """

    def __init__(self, parent, server_config: dict) -> None:
        """
        Initialize the server panel with specific server configuration.

        :param parent: The parent widget.
        :param server_config: Configuration details for the server.
        """
        super().__init__(parent)
        self.server_config = server_config

        self.setup_ui()

    def setup_ui(self) -> None:
        """
        Sets up the user interface components for the server panel.
        """
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, pady=(0, 10))

        # Initialize tabs with server configuration
        self.summary_tab = SummaryTab(self.notebook)
        self.commands_tab = CommandsTab(self.notebook)
        self.mods_tab = ModsTab(self.notebook)
        self.settings_tab = SettingsTab(self.notebook)

        # Add tabs to the notebook
        self.notebook.add(self.summary_tab, text="Summary")
        self.notebook.add(self.commands_tab, text="Commands")
        self.notebook.add(self.mods_tab, text="Mods")
        self.notebook.add(self.settings_tab, text="Settings")
