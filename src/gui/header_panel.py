import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class HeaderPanel(ttk.Frame):
    """
    GUI component representing the header panel of the application.
    """

    def __init__(self, parent, title: str = "Ark Ascended Cluster Manager") -> None:
        """
        Initialize the header panel with an optional title.

        :param parent: The parent widget.
        :param title: The title to display in the header panel.
        """
        super().__init__(parent)
        self.title = title
        self.setup_ui()

    def setup_ui(self) -> None:
        """
        Sets up the user interface components for the header panel.
        """
        # Label displaying the title of the program
        self.title_label = ttk.Label(self, text=self.title, bootstyle=PRIMARY)
        self.title_label.pack(side="left", padx=10, pady=10)

        # You can add more header-related widgets here later if needed
