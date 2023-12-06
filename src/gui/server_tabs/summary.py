import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from .scrollable_frame import ScrollableFrame


class SummaryTab(ScrollableFrame):
    """
    GUI component representing the summary tab within a server panel.
    """

    def __init__(self, parent) -> None:
        """
        Initialize the summary tab with specific server data.

        :param parent: The parent widget, typically a notebook tab.
        :param server_data: Data to display in the summary tab.
        """
        super().__init__(parent)
        self.server_data = {}

        self.setup_ui()

    def setup_ui(self) -> None:
        """
        Sets up the user interface components for the summary tab.
        """
        # Create and place your summary widgets inside self.inner_frame
        # Example label showing server status
        self.status_label = ttk.Label(
            self.inner_frame,
            text=f"Status: {self.server_data.get('status', 'Unknown')}",
        )
        self.status_label.pack(pady=10)

        # Example frame for server statistics
        self.stats_frame = ttk.Frame(self.inner_frame)
        self.stats_frame.pack(fill="both", expand=True)

        # Example labels inside stats_frame for detailed server data
        self.cpu_label = ttk.Label(
            self.stats_frame,
            text=f"CPU Usage: {self.server_data.get('cpu_usage', 'N/A')}",
        )
        self.cpu_label.pack(side="top", fill="x")
