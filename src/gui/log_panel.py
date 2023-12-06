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
        # Create a scrollbar
        self.scrollbar = ttk.Scrollbar(self)
        self.scrollbar.pack(side="right", fill="y")

        # Create the text widget with a scrollbar
        self.log_text = ttk.Text(
            self, state="disabled", yscrollcommand=self.scrollbar.set
        )
        self.log_text.pack(side="left", fill="both", expand=True, padx=10, pady=10)

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
