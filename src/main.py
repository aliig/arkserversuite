import customtkinter
from gui.main_window import MainWindow


def main() -> None:
    """
    Entry point for the application.
    Initializes the GUI and starts the application loop.
    """
    customtkinter.set_appearance_mode("dark")  # Set the theme to dark mode
    customtkinter.set_default_color_theme("blue")  # Set the default color theme to blue

    app = MainWindow()  # Create an instance of the main window
    app.mainloop()  # Start the application loop


if __name__ == "__main__":
    main()
