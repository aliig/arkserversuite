import yaml
import os


def load_config(config_path: str = "config.yml") -> dict:
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file '{config_path}' not found.")

    with open(config_path, "r") as stream:
        return yaml.safe_load(stream)


# If you want to have a default config loaded on import, you can use the following:
DEFAULT_CONFIG = load_config()
