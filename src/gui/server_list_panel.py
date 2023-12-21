import tkinter as tk
from typing import Callable, Dict

import ttkbootstrap as ttk

from global_context import global_context

from .dialog.add_server import AddServerDialog
from .dialog.copy_settings import CopySettingsDialog
from .dialog.select_server import SelectServerDialog


class ServerListPanel(ttk.Frame):
    """
    GUI component representing the list of servers and the server add button.
    """

    def __init__(self, parent, on_server_selected: Callable) -> None:
        """
        Initialize the ServerListPanel.

        :param parent: The parent widget.
        :param on_server_selected: Callback function to be called when a server is selected.
        """
        super().__init__(parent)
        self.setup_ui()
        self.on_server_selected = on_server_selected
        self.server_slots: set = set()
        self.database_manager = global_context.database_manager
        self.initialize_servers()

    def setup_ui(self) -> None:
        """
        Sets up the user interface components for the server list panel.
        """
        self.server_list_frame = ttk.Frame(self, bootstyle="secondary")
        self.server_list_frame.pack(
            fill="both", expand=True, padx=(0, 10), pady=(0, 10)
        )

        self.add_server_button = ttk.Button(
            self,
            text="Add Server",
            command=self.prompt_new_server,
            bootstyle="primary",
            width=30,
        )
        self.add_server_button.pack(padx=(0, 10))

    def initialize_servers(self):
        # Fetch existing servers from the database and create buttons
        existing_servers = self.database_manager.get_servers()
        for server in existing_servers:
            self.add_server_slot(server[0])  # Assuming server is a tuple

    def prompt_new_server(self) -> None:
        """
        Prompts the user to add a new server.
        """
        add_server_dialog = AddServerDialog(self)
        self.wait_window(add_server_dialog)

        server_name = add_server_dialog.get_server_name()
        if server_name:
            print(f"Adding new server '{server_name}'.")
            if len(self.server_slots) > 0:
                self.prompt_copy_settings(server_name)
            else:
                self.add_server_slot(server_name)

    def add_server_slot(self, server_name: str) -> None:
        """
        Adds a new slot for a server instance.
        """
        if server_name not in self.server_slots:
            try:
                self.database_manager.add_server(server_name)
                self.server_slots.add(server_name)
                self.create_server_button(server_name)
            except Exception as e:
                print(f"Error adding server: {e}")

    def create_server_button(self, server_name: str) -> None:
        """
        Creates and adds a button for the server.
        """
        server_button = ttk.Button(
            self.server_list_frame,
            text=server_name,
            bootstyle="warning",
            command=lambda: self.server_button_clicked(server_name),
        )
        server_button.pack(pady=1, fill="x")  # Add some padding between buttons

    def server_button_clicked(self, server_name: str) -> None:
        """
        Handles the event when a server button is clicked.
        """
        print(f"Server button for '{server_name}' clicked.")
        if self.on_server_selected:
            self.on_server_selected(server_name)

    def prompt_copy_settings(self, new_server_name: str) -> None:
        """
        Prompts the user whether to copy settings from another server.
        """
        copy_settings_dialog = CopySettingsDialog(self)
        self.wait_window(copy_settings_dialog)

        if copy_settings_dialog.should_copy_settings():
            self.prompt_select_server(new_server_name)
        else:
            self.add_server_slot(new_server_name)

    def prompt_select_server(self, new_server_name: str) -> None:
        """
        Prompts the user to select a server to copy settings from.
        """
        select_server_dialog = SelectServerDialog(self)
        self.wait_window(select_server_dialog)

        selected_server = select_server_dialog.get_selected_server()
        if selected_server:
            try:
                self.database_manager.copy_server_settings(
                    selected_server, new_server_name
                )
                self.add_server_slot(new_server_name)
            except Exception as e:
                print(f"Error copying server settings: {e}")
