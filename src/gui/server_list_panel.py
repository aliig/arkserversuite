import tkinter as tk
from typing import Callable, Dict

import ttkbootstrap as ttk

from .dialog.add_server import AddServerDialog
from .dialog.copy_settings import CopySettingsDialog
from .dialog.select_server import SelectServerDialog


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
        self.server_slots: set = set()

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
            self.server_slots.add(server_name)
            self.create_server_button(server_name)

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
        # Here you can define what should happen when a server button is clicked

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
            # Here you would copy the settings from the selected server
            # For now, we just add the new server tab
            self.add_server_slot(new_server_name)
