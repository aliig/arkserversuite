import os
from functools import cached_property

import yaml


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
            print(f"Error loading YAML file {file_path}: {e}")
            raise

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
        for k, v in u.items():
            if isinstance(v, dict):
                d[k] = ConfigLoader.recursive_update(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    @cached_property
    def merged_config(self):
        return self.recursive_update(self.default_config, self.custom_config)


DEFAULT_CONFIG = ConfigLoader().merged_config

print(f"Config settings: {DEFAULT_CONFIG}")
