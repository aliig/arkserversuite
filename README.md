# Ark Server Management Tool

A Python-based tool designed to automate and manage an ARK: Survival Evolved server instance.

## Features

- **Server Management**: Easily start, stop, and restart your ARK server.
- **Server Monitoring**: Checks if the server process is currently running.
- **Update Management**: Checks for updates and applies them automatically.
- **RCON Command Interface**: Send any RCON command to the server.

## Requirements

- Python 3.8 or higher
- `yaml` library for configuration management
- A running ARK: Survival Evolved server instance.

## Configuration

Before using, configure the server settings in `config.yaml`. This file contains essential settings, including paths, credentials, intervals, and other server-specific settings.

Example of `config.yaml`:
```
steamcmd:
  path: "/path/to/steamcmd.exe"
  username: "steam-username"
  app_id: 123456
  ...
```

## Usage

```bash
python server_management.py
```

This will start the management tool which will then manage your ARK server based on the configurations provided.

## Contribution

Feel free to fork the repository and submit pull requests. All contributions are welcome!

## License

This project is open-sourced and available under the [MIT License](LICENSE).
