import ttkbootstrap as ttk

from .header_panel import HeaderPanel
from .log_panel import LogPanel
from .server_list_panel import ServerListPanel
from .server_panel import ServerPanel


class MainWindow(ttk.Window):
    """
    The main application window that contains all the panels and frames.
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize the main window of the application.
        """
        super().__init__(*args, **kwargs)
        self.title("Ark Cluster Manager")
        self.geometry("1040x700")
        self.active_server_name = None
        self.setup_ui()

    def setup_ui(self) -> None:
        """
        Sets up the user interface components for the main window.
        """
        # Header Panel
        self.header_panel = HeaderPanel(self)
        self.header_panel.pack(side="top", fill="x")

        # Separator
        separator = ttk.Separator(self, orient="horizontal")
        separator.pack(
            side="top", fill="x", pady=10
        )  # Add some padding for visual spacing

        # PanedWindow for Main Content
        self.main_content_paned = ttk.Panedwindow(self, orient="horizontal")
        self.main_content_paned.pack(
            side="top", fill="both", expand=True, padx=10, pady=(0, 10)
        )  # Changed from 'bottom' to 'top'

        # Server List Panel
        self.server_list_panel = ServerListPanel(
            self.main_content_paned, self.set_active_server
        )
        self.main_content_paned.add(self.server_list_panel)

        # Right-side Frame
        self.right_side_frame = ttk.Frame(self.main_content_paned)
        self.main_content_paned.add(self.right_side_frame)

        # Right-side PanedWindow
        self.right_side_paned = ttk.Panedwindow(
            self.right_side_frame, orient="vertical"
        )
        self.right_side_paned.pack(fill="both", expand=True, padx=(10, 0))

        # Server Panel
        self.add_server_panel()

        # Log Panel
        self.log_panel = LogPanel(self.right_side_paned)
        # Set a smaller weight for LogPanel, so it takes less priority
        self.right_side_paned.add(self.log_panel, weight=1)

    def add_server_panel(self) -> None:
        """
        Creates and adds the ServerPanel to the right side PanedWindow.
        """
        if hasattr(self, "server_panel"):
            # Remove the existing server panel if it exists
            self.right_side_paned.forget(self.server_panel)

        self.server_panel = ServerPanel(self.right_side_paned, self.active_server_name)
        self.right_side_paned.add(self.server_panel, weight=2)

    def set_active_server(self, server_name: str) -> None:
        """
        Sets the name of the currently active server.
        """
        self.active_server_name = server_name
        self.add_server_panel()


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
