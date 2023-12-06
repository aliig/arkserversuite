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
        self.geometry("800x600")
        self.setup_ui()

    def setup_ui(self) -> None:
        """
        Sets up the user interface components for the main window.
        """
        # Header Panel
        self.header_panel = HeaderPanel(self)
        self.header_panel.pack(side="top", fill="x")

        # Main Content Frame
        self.main_content_frame = ttk.Frame(self)
        self.main_content_frame.pack(side="bottom", fill="both", expand=True)

        # Server List Panel
        self.server_list_panel = ServerListPanel(self.main_content_frame)
        self.server_list_panel.pack(side="left", fill="y")

        # Right-side Frame
        self.right_side_frame = ttk.Frame(self.main_content_frame)
        self.right_side_frame.pack(side="right", fill="both", expand=True)

        # Server Panel
        server_config = {}  # Placeholder for server configuration data
        self.server_panel = ServerPanel(self.right_side_frame, server_config)
        self.server_panel.pack(side="top", fill="both", expand=True)

        # Log Panel
        self.log_panel = LogPanel(self.right_side_frame)
        self.log_panel.pack(side="bottom", fill="x")


if __name__ == "__main__":
    app = MainWindow(themename="superhero")
    app.mainloop()
