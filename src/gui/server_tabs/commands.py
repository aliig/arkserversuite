import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from .scrollable_frame import ScrollableFrame

# from old.rcon import destroy_wild_dinos  # Import your function here


class CommandsTab(ScrollableFrame):
    """
    GUI component representing the commands tab within a server panel.
    """

    def __init__(self, parent) -> None:
        """
        Initialize the commands tab.

        :param parent: The parent widget, typically a notebook tab.
        """
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self) -> None:
        """
        Sets up the user interface components for the commands tab.
        """
        # Create and place your command buttons inside self.inner_frame

        # Example button for "Destroy Wild Dinos"
        self.destroy_dinos_button = ttk.Button(
            self.inner_frame,
            text="Destroy Wild Dinos",
            command=self.on_destroy_wild_dinos,
            bootstyle="danger",
        )
        self.destroy_dinos_button.pack(pady=10)

        # Add more buttons for other RCON commands here

    def on_destroy_wild_dinos(self) -> None:
        """
        Callback method for the 'Destroy Wild Dinos' button.
        """
        # Call the imported function to destroy wild dinos
        pass
        # destroy_wild_dinos()
        # You may want to add additional logic, like confirmation dialogs or status messages
