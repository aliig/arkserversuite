import customtkinter
from .server_tab import ServerTab
from .dialog.add_server import AddServerDialog
from .dialog.copy_settings import CopySettingsDialog
from .dialog.select_server import SelectServerDialog
from typing import Dict


class MainWindow(customtkinter.CTk):
    """
    Main window of the application, hosting the server tabs and other controls.
    """

    def __init__(self) -> None:
        """
        Initialize the main window with necessary components.
        """
        super().__init__()
        self.title("Ark Cluster Manager")
        self.geometry("800x600")

        self.server_tabs: Dict[str, ServerTab] = {}
        self.tab_control = customtkinter.CTkTabview(self)
        self.tab_control.pack(expand=True, fill="both", padx=20, pady=20)

        self.add_server_button = customtkinter.CTkButton(
            self, text="Add Server", command=self.prompt_new_server
        )
        self.add_server_button.pack(pady=10)

    def prompt_new_server(self) -> None:
        """
        Prompts the user to add a new server.
        """
        existing_server_names = list(self.server_tabs.keys())
        add_server_dialog = AddServerDialog(self, existing_server_names)
        self.wait_window(add_server_dialog)

        server_name = add_server_dialog.get_server_name()
        if server_name:
            if len(self.server_tabs) > 0:
                print(
                    f"Server '{server_name}' already exists. Prompting for copy settings."
                )
                self.prompt_copy_settings(server_name)
            else:
                print(f"Adding new server '{server_name}'.")
                self.add_server_tab(server_name, {"config": "new_server_config"})

    def prompt_copy_settings(self, new_server_name: str) -> None:
        """
        Prompts the user whether to copy settings from another server.
        """
        copy_settings_dialog = CopySettingsDialog(self)
        self.wait_window(copy_settings_dialog)

        if copy_settings_dialog.should_copy_settings():
            self.prompt_select_server(new_server_name)

    def prompt_select_server(self, new_server_name: str) -> None:
        """
        Prompts the user to select a server to copy settings from.
        """
        existing_server_names = list(self.server_tabs.keys())
        select_server_dialog = SelectServerDialog(self, existing_server_names)
        self.wait_window(select_server_dialog)

        selected_server = select_server_dialog.get_selected_server()
        if selected_server:
            # Here you would copy the settings from the selected server
            # For now, we just add the new server tab
            self.add_server_tab(
                new_server_name, {"config": f"copied_from_{selected_server}"}
            )

    def add_server_tab(self, server_name: str, server_config: Dict) -> None:
        """
        Adds a new tab for a server instance.
        """
        if server_name not in self.server_tabs:
            new_tab = ServerTab(self.tab_control.add(server_name), server_config)
            self.server_tabs[server_name] = new_tab

    def delete_server_tab(self, server_name: str) -> None:
        """
        Deletes a tab for a server instance.

        :param server_name: The name of the server instance to delete.
        """
        if server_name in self.server_tabs:
            self.tab_control.delete(server_name)
            del self.server_tabs[server_name]

    def rename_server_tab(self, old_name: str, new_name: str) -> None:
        """
        Renames a tab for a server instance.

        :param old_name: The current name of the server instance.
        :param new_name: The new name for the server instance.
        """
        if old_name in self.server_tabs and new_name not in self.server_tabs:
            self.tab_control.rename(old_name, new_name)
            self.server_tabs[new_name] = self.server_tabs.pop(old_name)

    # Additional methods for other tab management functionalities can be added here
