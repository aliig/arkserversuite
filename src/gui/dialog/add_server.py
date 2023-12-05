import re
import customtkinter
from .base import BaseDialog
from CTkMessagebox import CTkMessagebox


class AddServerDialog(BaseDialog):
    """
    Dialog to prompt user to name the server.
    """

    def __init__(self, parent, existing_server_names):
        super().__init__(parent, "Add Server")
        self.existing_server_names = existing_server_names
        self.server_name = None

        self.label = customtkinter.CTkLabel(self, text="Enter Server Name:")
        self.label.pack(pady=10)

        self.entry = customtkinter.CTkEntry(self)
        self.entry.pack(pady=10)
        self.entry.focus_set()

        self.confirm_button = customtkinter.CTkButton(
            self, text="Confirm", command=self.on_confirm
        )
        self.confirm_button.pack(pady=10)

    def on_confirm(self):
        entered_name = self.entry.get().strip()
        is_valid, message = self.is_valid_server_name(entered_name)
        if is_valid:
            self.server_name = entered_name
            self.destroy()
        else:
            CTkMessagebox(title="Invalid Server Name", message=message, icon="cancel")

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
