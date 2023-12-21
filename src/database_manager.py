import json
import sqlite3
import os
from typing import Any


class DatabaseManager:
    def __init__(self, db_path):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        with self.conn:
            # Server table
            self.conn.execute(
                """CREATE TABLE IF NOT EXISTS servers (
                    id INTEGER PRIMARY KEY,
                    server_name TEXT,
                    setting_key TEXT,
                    setting_value TEXT)"""
            )

            # Cluster settings table
            self.conn.execute(
                """CREATE TABLE IF NOT EXISTS cluster_settings (
                    id INTEGER PRIMARY KEY,
                    setting_key TEXT UNIQUE NOT NULL,
                    setting_value TEXT NOT NULL)"""
            )

    def add_column(self, table_name, column_name, data_type):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            existing_columns = [column[1] for column in cursor.fetchall()]
            if column_name in existing_columns:
                print(f"Column '{column_name}' already exists in table '{table_name}'.")
            else:
                self.conn.execute(
                    f"ALTER TABLE {table_name} ADD COLUMN {column_name} {data_type}"
                )

    def add_server(self, server_name):
        with self.conn:
            try:
                self.conn.execute(
                    "INSERT INTO servers (server_name, setting_key, setting_value) VALUES (?, ?, ?)",
                    (server_name, "default_setting", "default_value"),
                )
            except sqlite3.IntegrityError:
                print(f"Server '{server_name}' already exists.")

    def copy_server_settings(self, source_server_name, target_server_name):
        settings = self.conn.execute(
            "SELECT setting_key, setting_value FROM servers WHERE server_name=?",
            (source_server_name,),
        ).fetchall()
        with self.conn:
            for key, value in settings:
                self.conn.execute(
                    "INSERT INTO servers (server_name, setting_key, setting_value) VALUES (?, ?, ?)",
                    (target_server_name, key, value),
                )

    def get_servers(self):
        with self.conn:
            return self.conn.execute(
                "SELECT DISTINCT server_name FROM servers"
            ).fetchall()

    def update_cluster_setting(self, key, value):
        with self.conn:
            self.conn.execute(
                """INSERT INTO cluster_settings (setting_key, setting_value)
                   VALUES (?, ?)
                   ON CONFLICT(setting_key)
                   DO UPDATE SET setting_value = excluded.setting_value""",
                (key, value),
            )

    def get_cluster_setting(self, key):
        with self.conn:
            return self.conn.execute(
                "SELECT setting_value FROM cluster_settings WHERE setting_key = ?",
                (key,),
            ).fetchone()

    def get_server_value(self, server_name: str, setting_key: str) -> Any | None:
        """
        Fetches a setting value for a specified server based on the provided setting key.

        :param server_name: The name of the server to fetch settings from.
        :param setting_key: The key of the setting to query.
        :return: The value associated with the setting key for the specified server, or None if not found.
        """
        with self.conn:
            result = self.conn.execute(
                "SELECT setting_value FROM servers WHERE server_name = ? AND setting_key = ?",
                (server_name, setting_key),
            ).fetchone()
            return result[0] if result else None

    def update_server_value(
        self, server_name: str, setting_key: str, setting_value: str
    ):
        """
        Updates or inserts a setting value for a specified server.

        :param server_name: The name of the server for which to update or insert the setting.
        :param setting_key: The key of the setting to be updated or inserted.
        :param setting_value: The value to be set for the key.
        """
        with self.conn:
            self.conn.execute(
                """INSERT INTO servers (server_name, setting_key, setting_value)
                   VALUES (?, ?, ?)
                   ON CONFLICT(server_name, setting_key)
                   DO UPDATE SET setting_value = excluded.setting_value""",
                (server_name, setting_key, setting_value),
            )

    def print_all_data(self):
        print("Servers:")
        with self.conn:
            servers = self.conn.execute("SELECT * FROM servers").fetchall()
            for server in servers:
                print(server)

        print("\nCluster Settings:")
        with self.conn:
            settings = self.conn.execute("SELECT * FROM cluster_settings").fetchall()
            for setting in settings:
                print(setting)

    def get_all_data_as_json(self):
        data = {"servers": [], "cluster_settings": []}
        with self.conn:
            cursor = self.conn.cursor()

            # Fetch and format server data
            cursor.execute("SELECT * FROM servers")
            columns = [col[0] for col in cursor.description]
            for server in cursor.fetchall():
                data["servers"].append(dict(zip(columns, server)))

            # Fetch and format cluster settings data
            cursor.execute("SELECT * FROM cluster_settings")
            columns = [col[0] for col in cursor.description]
            for setting in cursor.fetchall():
                data["cluster_settings"].append(dict(zip(columns, setting)))

        return json.dumps(data, indent=4)

    def close(self):
        self.conn.close()


if __name__ == "__main__":
    db_manager = DatabaseManager("output/aacm.db")
    db_manager.print_all_data()  # Print all data for checking
    print(db_manager.get_all_data_as_json())
    db_manager.close()
