import requests

import os

API_KEY = os.getenv("CURSEFORGE_API_KEY")


def _get_installed_mod_version(file_path):
    try:
        with open(file_path, "rb") as file:
            content = file.read()
            # Assuming the version string follows a known pattern, e.g., "Version:1.2.3"
            # You might need to adjust this depending on the actual format

            return content

            start_marker = b"Version:"
            end_marker = b"\n"  # Assuming the version string ends with a newline

            start_index = content.find(start_marker)
            if start_index != -1:
                end_index = content.find(end_marker, start_index)
                version_string = content[start_index:end_index].decode("utf-8")
                return version_string
            else:
                return "Version information not found"
    except IOError as e:
        return f"Error opening file: {e}"


def _get_latest_mod_version(mod_id: int):
    headers = {"Accept": "application/json", "x-api-key": API_KEY}

    r = requests.get(f"https://api.curseforge.com/v1/mods/{mod_id}", headers=headers)

    print(r.json())


# mod_version = find_mod_version("output/test.ucas")
# print(mod_version)

print(_get_latest_mod_version(929420))
