import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class BaseDialog(tk.Toplevel):
    """
    Base class for modal dialog windows.
    """

    def __init__(self, parent, title: str, width: int = 300, height: int = 150):
        super().__init__(parent)
        self.transient(parent)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.grab_set()
        self.lift()

        # Center the window relative to the parent
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        x = parent_x + parent_width // 2 - width // 2
        y = parent_y + parent_height // 2 - height // 2
        self.geometry(f"+{x}+{y}")
