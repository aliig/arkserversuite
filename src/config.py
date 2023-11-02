import yaml
import os

def load_config(default_config_path: str = "config/config.yml", custom_config_path: str = "config/custom.yml") -> dict:
    # Load default config
    if not os.path.exists(default_config_path):
        raise FileNotFoundError(f"Default config file '{default_config_path}' not found.")
    with open(default_config_path, "r") as stream:
        config = yaml.safe_load(stream)

    # Load and override with custom config if it exists
    if os.path.exists(custom_config_path):
        with open(custom_config_path, "r") as stream:
            custom_config = yaml.safe_load(stream)
            # Override or update values with those from the custom config
            config.update(custom_config)

    print(config)
    return config

# Load the merged config (default with custom overrides) on import
DEFAULT_CONFIG = load_config()
