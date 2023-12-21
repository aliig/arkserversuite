import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from forms.server_settings import SERVER_SETTINGS
from forms.base import FieldType
from .scrollable_frame import ScrollableFrame
from gui.widgets.tooltip import ToolTip
from global_context import global_context


class SettingsTab(ScrollableFrame):
    """
    GUI component representing the settings tab within a server panel.
    """

    def __init__(self, parent) -> None:
        """
        Initialize the settings tab with specific server configuration.

        :param parent: The parent widget, typically a notebook tab.
        """
        super().__init__(parent)
        self.server_config = {}
        self.fields = {}
        self.database_manager = global_context.database_manager

        self.setup_ui()
        self.load_settings_from_database()

    def setup_ui(self) -> None:
        """
        Sets up the user interface components for the settings tab.
        """
        # Create a labeled frame for server settings
        self.server_settings_frame = ttk.LabelFrame(
            self.inner_frame, text="Server Settings", padding=10
        )
        self.server_settings_frame.pack(fill="both", expand=True, pady=10)

        # Add setting fields to the server settings frame
        for field in SERVER_SETTINGS:
            self.add_setting_field(field, self.server_settings_frame)

    def add_setting_field(self, field, parent_frame) -> None:
        """
        Adds a setting field to the UI based on the FormField specification.

        :param field: The FormField instance containing field specifications.
        :param parent_frame: The parent frame to which the field should be added.
        """
        frame = ttk.Frame(parent_frame)
        frame.pack(fill="x", expand=True, pady=2)

        label = ttk.Label(frame, text=f"{field.field_name}:")
        label.pack(side="left", padx=5)

        widget = None  # Initialize a variable to hold the widget

        if field.field_type == FieldType.TEXT:
            widget = ttk.Entry(
                frame,
                textvariable=ttk.StringVar(
                    value=self.get_field_value(field.field_name)
                ),
            )
            widget.pack(side="right", fill="x", expand=True, padx=5)
            self.fields[field.field_name] = widget
        elif field.field_type == FieldType.CHECKBOX:
            var = ttk.BooleanVar(
                value=self.get_field_value(field.field_name).lower() == "true"
            )
            widget = ttk.Checkbutton(
                frame,
                variable=var,
                command=lambda: self.update_field_value(field.field_name, var.get()),
            )
            widget.pack(side="right", padx=5)
            self.fields[field.field_name] = var
        # Add more widget types here as needed

        if widget:
            ToolTip(widget, text=field.tooltip)  # Attach tooltip to the widget

    def get_field_value(self, field_name):
        """
        Retrieves the value of a field from the database.

        :param field_name: The name of the field.
        :return: The value of the field from the database.
        """
        # Retrieve the value from the database using the field name
        return self.database_manager.get_field_value(field_name)

    def update_field_value(self, field_name, value):
        """
        Updates the value of a field in the database.

        :param field_name: The name of the field.
        :param value: The new value of the field.
        """
        # Update the value in the database using the field name and new value
        self.database_manager.update_field_value(field_name, value)

    def load_settings_from_database(self):
        """
        Loads the settings from the database and updates the form fields.
        """
        settings = self.database_manager.get_all_settings()
        for field_name, value in settings.items():
            if field_name in self.fields:
                widget = self.fields[field_name]
                if isinstance(widget, ttk.Entry):
                    widget.delete(0, "end")
                    widget.insert(0, value)
                elif isinstance(widget, ttk.BooleanVar):
                    widget.set(value.lower() == "true")

    def get_settings(self) -> dict[str, str | bool]:
        """
        Retrieves the settings from the UI fields.

        :return: A dictionary of settings with field names as keys.
        """
        settings = {}
        for field_name, widget in self.fields.items():
            if isinstance(widget, ttk.Entry):
                settings[field_name] = widget.get()
            elif isinstance(widget, ttk.BooleanVar):
                settings[field_name] = widget.get()
        return settings
