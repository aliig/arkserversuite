import yaml
import os
from functools import cached_property


class ConfigLoader:
    def __init__(
        self,
        default_config_path: str = "config/config.yml",
        custom_config_path: str = "config/custom.yml",
    ):
        self.default_config_path = default_config_path
        self.custom_config_path = custom_config_path

    @cached_property
    def default_config(self):
        if not os.path.exists(self.default_config_path):
            raise FileNotFoundError(
                f"Default config file '{self.default_config_path}' not found."
            )
        with open(self.default_config_path, "r") as stream:
            return yaml.safe_load(stream)

    @cached_property
    def custom_config(self):
        if os.path.exists(self.custom_config_path):
            with open(self.custom_config_path, "r") as stream:
                return yaml.safe_load(stream)
        return {}

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
