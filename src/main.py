import ttkbootstrap as ttk

from global_context import global_context
from gui.main_window import MainWindow


def main() -> None:
    """
    Entry point for the application.
    Initializes the GUI and starts the application loop.
    """

    global_context.setup_database("output/aacm.db")

    app = MainWindow(themename="darkly")
    app.mainloop()  # Start the application loop


if __name__ == "__main__":
    main()
