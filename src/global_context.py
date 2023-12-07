import logging

from database_manager import DatabaseManager


class GlobalContext:
    def __init__(self):
        self.database_manager = None

    def setup_database(self, db_path):
        self.database_manager = DatabaseManager(db_path)  # Initialize DatabaseManager


# Instantiate the global context
global_context = GlobalContext()
