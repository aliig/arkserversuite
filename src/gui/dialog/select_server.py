import customtkinter
from .base import BaseDialog


class SelectServerDialog(BaseDialog):
    """
    Dialog to select a server from a dropdown list.
    """

    def __init__(self, parent, server_names):
        super().__init__(parent, "Select Server")

        self.selected_server = None

        self.label = customtkinter.CTkLabel(self, text="Select a server:")
        self.label.pack(pady=10)

        self.dropdown = customtkinter.CTkOptionMenu(self, values=server_names)
        self.dropdown.pack(pady=10)
        self.dropdown.focus_set()

        self.confirm_button = customtkinter.CTkButton(
            self, text="Confirm", command=self.on_confirm
        )
        self.confirm_button.pack(pady=10)

    def on_confirm(self):
        self.selected_server = self.dropdown.get()
        self.destroy()

    def get_selected_server(self):
        return self.selected_server
