from config import DEFAULT_CONFIG
import configparser
import os


def _ini_filepath(file):
    return os.path.join(
        DEFAULT_CONFIG["server"]["install_path"],
        "ShooterGame\Saved\Config\WindowsServer",
        f"{file}.ini",
    )


def _get_ini(file_path):
    # Create a ConfigParser object
    config = configparser.ConfigParser()
    # Read the INI file
    config.read(file_path)
    return config


def _update_ini(file, section, settings):
    # Get the current configuration
    filepath = _ini_filepath(file)
    config = _get_ini(filepath)

    # If settings is a dictionary, update all key/value pairs
    if isinstance(settings, dict):
        for key, val in settings.items():
            config[section][key] = str(val)
    # If settings is a tuple, update the single key/value pair
    elif isinstance(settings, tuple):
        key, val = settings
        config[section][key] = str(val)
    else:
        raise ValueError(
            "Settings must be either a dictionary of key/value pairs or a tuple representing a key/value pair."
        )

    # Write the updated configuration back to the file
    with open(filepath, "w") as configfile:
        config.write(configfile)


def update(file, section, settings):
    _update_ini(file, section, settings)
