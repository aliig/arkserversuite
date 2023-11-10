# Ark Ascended Dedicated Server Suite

## Overview

Ark Ascended Dedicated Server Suite is a Python-based automation tool for managing an ARK Survival Ascended server. It automates server updates, restarts, and other maintenance tasks, and provides Discord integration for real-time notifications and logs.

## Key Features

- **Automated Server Management**: Streamlines ARK server operations with automated updates, restarts, and maintenance tasks.

- **Discord Integration**: Sends real-time notifications for server events, player activities, and chat messages directly to a Discord server.

- **Dynamic INI Configuration**: Custom Ark INI parser allows for complex configuration changes, including handling duplicate keys, directly from `config.yml`.

- **Backup and Restore**: Automatically backs up server configuration files before making changes, with timestamped backups for easy rollback.

- **SteamCMD Automation**: Integrates with SteamCMD to manage server updates, with the ability to download and set up SteamCMD if not already installed.

- **Scheduled Tasks**: Configurable tasks for server maintenance, such as destroying wild dinos, sending announcements, and checking for stale server status.

- **Welcome Messages**: Will send any users connecting to the server a welcome message. (derived from config.yml -> tasks/announcement/description)

- **Customizable Server Settings**: Tailor server settings to specific needs, including server name, map, player limits, and more, through an easy-to-edit configuration file.

- **Stale Server Handling**: Monitors server activity and can automatically restart an empty or stale server based on predefined thresholds.

## Usage

### Requirements

- **Knowledge of ARK Server Management**: Familiarity with running and managing ARK servers is essential. New users should refer to external tutorials for basic server setup and management.

- **Port Forwarding**: Proper network configuration is required to allow external connections to the ARK server. Users must know how to forward ports on their network router.

- **Stable Internet Connection**: A reliable internet connection is required for server updates, player connectivity, and Discord integration features.

- **Correct Server Settings**: Requires correct file paths, etc. in the `config.yml`` file.

### Running the Release Executable

For most users, it is recommended to use the pre-built `arkserversuite.exe` executable from the latest release.

1. Download the latest release from the [releases page](https://github.com/aliig/arkserversuite/releases) and extract the .zip file.
2. Run the executable file. Windows may display an "unknown publisher" security warning. You can proceed by clicking "More info" and then "Run anyway" to start the program.
3. For better insight into the program's activity, especially if you encounter any issues, it is advised to run the executable from a command prompt or PowerShell window. Navigate to the directory containing `arkserversuite.exe` and execute it by typing:

    ```cmd
    .\arkserversuite.exe
    ```

### Running from Source

For those interested in running the bleeding-edge version from GitHub or wishing to contribute to the project, follow these steps:

1. Ensure you have [Miniconda](https://docs.conda.io/en/latest/miniconda.html) installed on your server.
2. Clone the repository:

    ```bash
    git clone https://github.com/aliig/arkserversuite.git
    ```

3. Navigate to the cloned directory and create a new Conda environment using the `environment.yml` file:

    ```bash
    conda env create -f environment.yml
    ```

4. Activate the Conda environment:

    ```bash
    conda activate ark
    ```

5. Run the program from the source:

    ```bash
    python src/main.py
    ```

Please note that running from source may require additional steps such as setting up the development environment and dealing with potential dependencies or issues that arise from the latest changes in the codebase.

### Configuration

- Modify `config/config.yml` to your liking
- You can also create a file at `config/custom.yml` if you wish to override default configurations without altering the original `config.yml`. It will read `config.yml` by default and override anything specified in `custom.yml`.

### Disclaimer

Use this program at your own risk. I have tested it and used it for my personal ASA server, but I haven't been able to test every configuration change, etc. For example, it will modify your ARK config .ini files to implement server settings, but before it does it will save backups to the output directory.

## Roadmap
- Implement a GUI for easier use
- Manage server backups
- Hotkeys for rcon commands like destroywilddinos, saveworld, etc.

## Contributing
Contributors are welcome to extend the functionality of the program. Please ensure you follow best practices and keep the project structure and coding style consistent.

## PvE Server
Feel free to join my hosted ASA server--just search "Brohana" on unofficial. Here is the Discord server for support and community discussions. https://discord.gg/BsH25X3pTB

## License
This project is open-sourced under the MIT License.
