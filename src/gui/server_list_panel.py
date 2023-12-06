import tkinter as tk
from typing import Callable, Dict

import ttkbootstrap as ttk


class ServerListPanel(ttk.Frame):
    """
    GUI component representing the list of servers and the server add button.
    """

    def __init__(self, parent) -> None:
        """
        Initialize the server list panel.

        :param parent: The parent widget.
        :param add_server_callback: The callback function to execute when the add server button is clicked.
        """
        super().__init__(parent)

        self.setup_ui()

    def setup_ui(self) -> None:
        """
        Sets up the user interface components for the server list panel.
        """
        self.server_listbox = tk.Listbox(self)
        self.server_listbox.pack(fill="both", expand=True, padx=10, pady=10)

        self.add_server_button = ttk.Button(
            self,
            text="Add Server",
            command=self.add_server,
            bootstyle="success",
        )
        self.add_server_button.pack(padx=10, pady=10)

    def add_server(self) -> None:
        """
        Placeholder method for adding a server.
        """
        # This method should be connected to actual functionality to add a server
        pass

    def update_server_list(self, servers: Dict) -> None:
        """
        Update the server listbox with the list of servers.

        :param servers: A dictionary of server names and statuses.
        """
        # Clear the listbox
        self.server_listbox.delete(0, "end")

        # Add servers to the listbox
        for server_name, server_status in servers.items():
            self.server_listbox.insert("end", f"{server_name} - {server_status}")
