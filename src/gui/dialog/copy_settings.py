import customtkinter
from .base import BaseDialog


class CopySettingsDialog(BaseDialog):
    """
    Dialog to prompt user whether they want to copy settings from another server.
    """

    def __init__(self, parent):
        super().__init__(parent, "Copy Settings")

        self.copy_settings = False

        self.label = customtkinter.CTkLabel(
            self, text="Copy settings from another server?"
        )
        self.label.pack(pady=10)

        self.yes_button = customtkinter.CTkButton(self, text="Yes", command=self.on_yes)
        self.yes_button.pack(pady=5)

        self.no_button = customtkinter.CTkButton(self, text="No", command=self.on_no)
        self.no_button.pack(pady=5)

    def on_yes(self):
        self.copy_settings = True
        self.destroy()

    def on_no(self):
        self.destroy()

    def should_copy_settings(self):
        return self.copy_settings
