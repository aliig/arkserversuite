import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class LogPanel(ttk.Frame):
    """
    GUI component representing the log output area of the application.
    """

    def __init__(self, parent) -> None:
        """
        Initialize the log panel.

        :param parent: The parent widget.
        """
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self) -> None:
        """
        Sets up the user interface components for the log panel.
        """
        # Create an inner frame with padding
        inner_frame = ttk.Frame(self)
        inner_frame.pack(fill="both", expand=True, pady=(10, 0))

        # Create a scrollbar in the inner frame
        self.scrollbar = ttk.Scrollbar(inner_frame)
        self.scrollbar.pack(side="right", fill="y")

        # Create the text widget with a scrollbar in the inner frame
        self.log_text = ttk.Text(
            inner_frame, state="disabled", yscrollcommand=self.scrollbar.set, height=6
        )
        self.log_text.pack(side="left", fill="both", expand=True)

        # Link the scrollbar to the text widget
        self.scrollbar.config(command=self.log_text.yview)

    def add_log_entry(self, message: str) -> None:
        """
        Adds a log entry to the log text widget.

        :param message: The log message to be added.
        """
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{message}\n")
        self.log_text.configure(state="disabled")
        self.log_text.see("end")
