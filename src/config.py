import os
from functools import cached_property

import yaml
from tzlocal import get_localzone


class ConfigLoader:
    def __init__(
        self,
        default_config_path: str = "config/config.yml",
        custom_config_path: str = "config/custom.yml",
    ):
        self.default_config_path = default_config_path
        self.custom_config_path = custom_config_path

    def load_yaml_with_backslash_handling(self, file_path):
        """Load YAML file with handling for backslashes in strings."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                file_content = file.read().replace("\\", "\\\\")
            return yaml.safe_load(file_content)
        except yaml.YAMLError as e:
            raise RuntimeError(f"Error loading YAML file {file_path}: {e}")

    @cached_property
    def default_config(self):
        """Load the default (required) configuration."""
        if not os.path.exists(self.default_config_path):
            raise FileNotFoundError(
                f"Default config file '{self.default_config_path}' not found."
            )
        return self.load_yaml_with_backslash_handling(self.default_config_path)

    @cached_property
    def custom_config(self):
        """Load the custom (optional) configuration if available."""
        if os.path.exists(self.custom_config_path):
            return self.load_yaml_with_backslash_handling(self.custom_config_path)
        return {}  # Return an empty dictionary if custom config does not exist

    @staticmethod
    def recursive_update(d, u):
        if u:
            for k, v in u.items():
                if isinstance(v, dict):
                    d[k] = ConfigLoader.recursive_update(d.get(k, {}), v)
                else:
                    d[k] = v
        return d

    def validate_tasks(self, tasks_config):
        """Validate the tasks configuration."""
        for task_name, task in tasks_config.items():
            if not task.get("enable", False):
                continue  # Skip validation if the task is not enable

            # Validate warning times
            interval_hours = task.get("interval", 0)
            if "warnings" in task and task["warnings"] and task.get("enable", False):
                max_warning_minutes = max(task.get("warnings", []), default=0)
                if max_warning_minutes and max_warning_minutes >= interval_hours * 60:
                    raise ValueError(
                        f"Maximum warning time for '{task_name}' exceeds the interval time."
                    )

            # Validate blackout period
            blackout = task.get("blackout_period", {})
            start = blackout.get("start")
            end = blackout.get("end")
            if start and end and start == end:
                raise ValueError(
                    f"Blackout period start and end are the same for '{task_name}'."
                )

    def validate_config(self, config):
        """Validate the merged configuration."""
        required_fields = {
            "server": ["name", "ip_address", "port"],
        }
        optional_fields_with_defaults = {
            "server": {
                "port": 7777,
                "max_players": 20,
                "rcon_port": 32330,
                "map": "TheIsland_WP",
                "timezone": str(get_localzone()),
            },
            # Add other optional fields with their default values here
        }

        for section, fields in required_fields.items():
            if section not in config:
                raise ValueError(f"Section '{section}' is missing in the config.")

            for field in fields:
                if field not in config[section]:
                    raise ValueError(
                        f"Required field '{field}' is missing in the '{section}' section."
                    )

        for section, fields in optional_fields_with_defaults.items():
            if section in config:
                for field, default in fields.items():
                    config[section].setdefault(field, default)

        # Validate tasks
        if "tasks" in config:
            self.validate_tasks(config["tasks"])

    @cached_property
    def merged_config(self):
        merged = self.recursive_update(self.default_config, self.custom_config)
        self.validate_config(merged)
        return merged


class TestLoader(ConfigLoader):
    @property
    def default_config(self):
        print(f"Loading default config from {self.default_config_path}")
        return self.load_yaml_with_backslash_handling(self.default_config_path)

    @property
    def custom_config(self):
        print(f"Loading custom config from {self.custom_config_path}")
        return (
            self.load_yaml_with_backslash_handling(self.custom_config_path)
            if os.path.exists(self.custom_config_path)
            else {}
        )


CONFIG = ConfigLoader().merged_config
OUTDIR = CONFIG["advanced"].get("output_directory", "output")
os.makedirs(OUTDIR, exist_ok=True)
