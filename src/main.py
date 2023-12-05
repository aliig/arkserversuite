import ttkbootstrap as ttk
from gui.main_window import MainWindow


def main() -> None:
    """
    Entry point for the application.
    Initializes the GUI and starts the application loop.
    """
    # Create an instance of the main window with a specific ttkbootstrap theme

    app = MainWindow(themename="superhero")
    app.mainloop()  # Start the application loop


if __name__ == "__main__":
    main()
