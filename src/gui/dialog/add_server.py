import re
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from .base import BaseDialog
from tkinter import messagebox


class AddServerDialog(BaseDialog):
    """
    Dialog to prompt user to name the server.
    """

    def __init__(self, parent, existing_server_names):
        super().__init__(parent, "Add Server")
        self.existing_server_names = existing_server_names
        self.server_name = None

        self.label = ttk.Label(self, text="Enter Server Name:")
        self.label.pack(pady=10)

        # Register the validation callback
        validate_command = self.register(self.validate_server_name)

        self.entry = ttk.Entry(
            self, validate="focusout", validatecommand=(validate_command, "%P")
        )
        self.entry.pack(pady=10)
        self.entry.focus_set()

        self.confirm_button = ttk.Button(
            self, text="Confirm", command=self.on_confirm, bootstyle=PRIMARY
        )
        self.confirm_button.pack(pady=10)

    def validate_server_name(self, name: str) -> bool:
        """
        Validates the server name.
        """
        is_valid, _ = self.is_valid_server_name(name)
        if not is_valid:
            self.entry.configure(bootstyle=DANGER)
        else:
            self.entry.configure(bootstyle=DEFAULT)
        return is_valid

    def on_confirm(self):
        entered_name = self.entry.get().strip()
        is_valid, message = self.is_valid_server_name(entered_name)
        if is_valid:
            self.server_name = entered_name
            self.destroy()
        else:
            messagebox.showerror("Invalid Server Name", message)

    def is_valid_server_name(self, name: str) -> (bool, str):
        """
        Validates the server name.
        Returns a tuple (is_valid, message).
        """
        if name in self.existing_server_names:
            return False, "Server name already exists. Please choose a different name."

        if not re.match(r"^[A-Za-z0-9_-]+$", name):
            return (
                False,
                "Server name can only contain alphanumeric characters, hyphens, and underscores.",
            )

        return True, ""

    def get_server_name(self):
        return self.server_name
