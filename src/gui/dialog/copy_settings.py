import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from .base import BaseDialog


class CopySettingsDialog(BaseDialog):
    """
    Dialog to prompt user whether they want to copy settings from another server.
    """

    def __init__(self, parent):
        super().__init__(parent, "Copy Settings")

        self.copy_settings = False

        self.label = ttk.Label(self, text="Copy settings from another server?")
        self.label.pack(pady=10)

        self.yes_button = ttk.Button(
            self, text="Yes", command=self.on_yes, bootstyle=SUCCESS
        )
        self.yes_button.pack(pady=5)

        self.no_button = ttk.Button(
            self, text="No", command=self.on_no, bootstyle=DANGER
        )
        self.no_button.pack(pady=5)

    def on_yes(self):
        self.copy_settings = True
        self.destroy()

    def on_no(self):
        self.destroy()

    def should_copy_settings(self):
        return self.copy_settings
