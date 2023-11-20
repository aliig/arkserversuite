import os
import shutil
from collections import defaultdict
from configparser import RawConfigParser
from datetime import datetime
from typing import Any

from config import DEFAULT_CONFIG
from logger import get_logger

logger = get_logger(__name__)


class CustomConfigParser(RawConfigParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sections = defaultdict(list)
        # Preserve the case of options with this line:
        self.optionxform = str

    def _read(self, fp, fpname):
        """Parse a sectioned configuration file."""
        cursect = None  # None, or a dictionary
        sectname = None
        optname = None
        lineno = 0
        e = None  # None, or an exception
        for lineno, line in enumerate(fp, start=1):
            comment_start = line.find("#")
            if comment_start != -1:
                line = line[:comment_start]
            if not (line := line.strip()):
                continue  # skip blank lines
            if line[0] in "[]":  # a section header or continuation
                if line[-1] != "]":
                    raise ValueError(
                        "Malformed section header", line, "line %d." % lineno
                    )
                sectname = line[1:-1].strip()
                if sectname in self._sections:
                    cursect = self._sections[sectname]
                else:
                    cursect = self._sections[sectname] = []
            elif cursect is None:
                raise ValueError("No section header before", line, "line %d." % lineno)
            else:  # an option line
                mo = self.OPTCRE.match(line)
                if mo:
                    optname, vi, optval = mo.group("option", "vi", "value")
                    if not optname:
                        e = self._handle_error(e, fpname, lineno, line)
                    optname = self.optionxform(optname.rstrip())
                    if (
                        vi in ("=", ":")
                        and ";" in optval
                        and not optval.strip().startswith('"')
                    ):
                        pos = optval.find(";")
                        if pos != -1 and optval[pos - 1].isspace():
                            optval = optval[:pos]
                    optval = optval.strip()
                    # This check is the only change we make to allow duplicates
                    cursect.append((optname, optval))
                else:
                    # a non-fatal parsing error occurred. set up the
                    # exception but keep going. the exception will be
                    # raised at the end of the file and will contain a
                    # list of all malformed lines
                    e = self._handle_error(e, fpname, lineno, line)
        # if any parsing errors occurred, raise an exception
        if e:
            raise e

    def get(self, section, option):
        """Get an option value for the named section."""
        opts = self._sections.get(section, [])
        if not opts:
            raise ValueError("Section [%s] not found." % section)
        for name, value in opts:
            if name == option:
                return value
        raise ValueError("Option '%s' not found in section [%s]." % (option, section))

    def getlist(self, section, option):
        """Get a list of values for the named option."""
        return [
            value for name, value in self._sections.get(section, []) if name == option
        ]

    def set(self, section, option, value):
        """Set an option."""
        if not section:
            raise ValueError("Section name is required.")

        option = self.optionxform(option)  # Preserve case

        # Create the section if it doesn't exist
        if section not in self._sections:
            self._sections[section] = []

        if value is None:
            value = ""

        # Find the tuple with the matching option and replace its value
        # If the option does not exist, append a new tuple
        option_found = False
        for i, (optname, _) in enumerate(self._sections[section]):
            if optname == option:
                self._sections[section][i] = (option, value)
                option_found = True
                break

        if not option_found:
            self._sections[section].append((option, value))

    def write(self, fp):
        """Write an .ini-format representation of the configuration state."""
        for section, options in self._sections.items():
            fp.write("[{}]\n".format(section))
            for key, value in options:
                # Write the key=value without spaces around the equal sign
                fp.write("{}={}\n".format(key, value))
            fp.write("\n")


def ini_file(file) -> tuple[bool, str]:
    path = os.path.join(
        DEFAULT_CONFIG["server"]["install_path"],
        "ShooterGame/Saved/Config/WindowsServer",
        f"{file}.ini",
    )
    exists = os.path.isfile(path)
    return path, exists


def _save_backup(file):
    filepath, exists = ini_file(file)
    if not exists:
        logger.warning(f"{file}.ini not found at {filepath}, no backup will be created")
    else:
        # Save a backup of the current configuration
        file_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filepath = os.path.join(
            DEFAULT_CONFIG["advanced"].get("output_directory", "output"),
            "backup",
            "config",
            f"{file}.ini_{file_timestamp}",
        )
        os.makedirs(os.path.dirname(backup_filepath), exist_ok=True)
        shutil.copy(filepath, backup_filepath)
        logger.debug(f"Saved backup of {file}.ini to {backup_filepath}")


def _update_setting(file, section, settings):
    # Get the current configuration
    filepath, exists = ini_file(file)

    # Create an instance of the custom parser
    config = CustomConfigParser()

    # Check if the INI file exists, create it if it doesn't
    if not exists:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            pass  # Create an empty file

    # Read the INI file
    with open(filepath, "r") as f:
        config.read_file(f)

    # If settings is a dictionary, update all key/value pairs
    if isinstance(settings, dict):
        for key, val in settings.items():
            logger.debug(f"{key} = {val}")
            if val is None:
                val = ""
            # Use the custom set method to handle duplicates
            config.set(section, key, str(val))
            logger.debug(f"Updated {file}.ini {section} {key} = {val}")
    else:
        raise ValueError("Settings must be a dictionary of key/value pairs.")

    # Write the updated configuration back to the file
    with open(filepath, "w") as configfile:
        config.write(configfile)


def _update_from_config_overrides():
    if "config_overrides" in DEFAULT_CONFIG:
        for file, sections in DEFAULT_CONFIG["config_overrides"].items():
            for section, settings in sections.items():
                _update_setting(file, section, settings)


def _update_from_server_settings():
    game_user_settings_overrides: dict[str, dict[str, Any]] = {
        "ServerSettings": {
            "ServerPassword": DEFAULT_CONFIG["server"]["password"],
            "ServerAdminPassword": DEFAULT_CONFIG["server"]["admin_password"],
            "RCONPort": DEFAULT_CONFIG["server"]["rcon_port"],
            "RCONEnabled": True,
        },
        "SessionSettings": {
            "SessionName": DEFAULT_CONFIG["server"]["name"],
            "MULTIHOME": DEFAULT_CONFIG["server"]["ip_address"],
            "Port": DEFAULT_CONFIG["server"]["port"],
            "QueryPort": DEFAULT_CONFIG["server"]["query_port"],
        },
        "/Script/Engine.GameSession": {
            "MaxPlayers": DEFAULT_CONFIG["server"]["max_players"]
        },
        "MultiHome": {"MultiHome": True},
    }
    for section, settings in game_user_settings_overrides.items():
        _update_setting("GameUserSettings", section, settings)


def update_ark_configs():
    for file in ["GameUserSettings", "Game"]:
        _save_backup(file)
    # update the ARK config .ini files based on specific set config.yml overrides
    _update_from_config_overrides()
    # update the ARK config .ini files based on server settings in config.yml
    _update_from_server_settings()


if __name__ == "__main__":
    update_ark_configs()
