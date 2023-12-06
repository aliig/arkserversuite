import tkinter as tk

import ttkbootstrap as ttk
from ttkbootstrap import Style


class ToolTip(object):
    """
    A tooltip that appears when hovering over a widget.
    """

    def __init__(self, widget, text="widget info"):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

        # Binding enter and leave events
        self.widget.bind("<Enter>", self.showtip)
        self.widget.bind("<Leave>", self.hidetip)

    def showtip(self, event):
        "Display the tooltip"
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        # Explicitly setting background and foreground colors
        label = ttk.Button(tw, text=self.text, bootstyle="info")
        label.pack(ipadx=1)

    def hidetip(self, event):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()
