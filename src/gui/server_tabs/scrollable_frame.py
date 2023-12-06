import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class ScrollableFrame(ttk.Frame):
    """
    A scrollable frame used to contain other widgets.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.scrollbar = ttk.Scrollbar(self)
        self.scrollbar.pack(side="right", fill="y", expand=False)

        self.canvas = ttk.Canvas(self, yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scrollbar.config(command=self.canvas.yview)

        self.inner_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        self.inner_frame.bind("<Configure>", self.on_frame_configure)

    def on_frame_configure(self, event=None):
        """
        Reset the scroll region to encompass the inner frame.
        """
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
