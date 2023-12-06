import tkinter as tk

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from .base import BaseDialog


class SelectServerDialog(BaseDialog):
    """
    Dialog to select a server from a dropdown list.
    """

    def __init__(self, parent):
        super().__init__(parent, "Select Server")

        self.selected_server = None

        self.label = ttk.Label(self, text="Select a server:")
        self.label.pack(pady=10)

        self.server_var = tk.StringVar(self)
        self.dropdown = ttk.OptionMenu(self, self.server_var, *parent.server_slots)
        self.dropdown.pack(pady=10)
        self.dropdown.focus_set()

        self.confirm_button = ttk.Button(
            self, text="Confirm", command=self.on_confirm, bootstyle=PRIMARY
        )
        self.confirm_button.pack(pady=10)

    def on_confirm(self):
        self.selected_server = self.server_var.get()
        self.destroy()

    def get_selected_server(self):
        return self.selected_server
