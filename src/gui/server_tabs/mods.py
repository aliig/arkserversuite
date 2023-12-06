import tkinter as tk

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from .scrollable_frame import ScrollableFrame


class ModsTab(ScrollableFrame):
    """
    GUI component representing the mods tab within a server panel.
    """

    def __init__(self, parent) -> None:
        """
        Initialize the mods tab with specific server mods information.

        :param parent: The parent widget, typically a notebook tab.
        :param server_mods: Information about mods for the server.
        """
        super().__init__(parent)
        self.server_mods = {}

        self.setup_ui()

    def setup_ui(self) -> None:
        """
        Sets up the user interface components for the mods tab.
        """
        # Create and place your mods management widgets inside self.inner_frame

        # Example section for listing mods
        self.mods_list_frame = ttk.LabelFrame(
            self.inner_frame, text="Available Mods", padding=10
        )
        self.mods_list_frame.pack(fill="both", expand=True, pady=10)

        # Example listbox to show available mods
        self.mods_listbox = tk.Listbox(self.mods_list_frame)
        self.mods_listbox.pack(side="left", fill="both", expand=True)

        # Scrollbar for mods listbox
        self.mods_scrollbar = ttk.Scrollbar(
            self.mods_list_frame, command=self.mods_listbox.yview
        )
        self.mods_scrollbar.pack(side="right", fill="y")
        self.mods_listbox.config(yscrollcommand=self.mods_scrollbar.set)

        # Populate the listbox with mods (placeholder)
        for mod in self.server_mods.get("mods", []):
            self.mods_listbox.insert("end", mod)

        # Example controls for mod actions
        self.controls_frame = ttk.Frame(self.inner_frame)
        self.controls_frame.pack(fill="x", expand=False, pady=10)

        self.enable_mod_button = ttk.Button(
            self.controls_frame, text="Enable Mod", command=self.enable_mod
        )
        self.enable_mod_button.pack(side="left", padx=5)

        self.disable_mod_button = ttk.Button(
            self.controls_frame, text="Disable Mod", command=self.disable_mod
        )
        self.disable_mod_button.pack(side="left", padx=5)

        # Additional functionalities can be added as needed,
        # such as configuring individual mods, updating them, etc.

    def enable_mod(self) -> None:
        """
        Method to enable a selected mod.
        """
        # Logic to enable the selected mod goes here
        pass

    def disable_mod(self) -> None:
        """
        Method to disable a selected mod.
        """
        # Logic to disable the selected mod goes here
        pass
