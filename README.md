# Ark Ascended Dedicated Server Suite

## Overview

Ark Ascended Dedicated Server Suite is a Python-based automation tool for managing an ARK Survival Ascended server. It automates server updates, restarts, and other maintenance tasks, and provides Discord integration for real-time notifications and logs.

## Features

- Automated server updates and restarts.
- Scheduled tasks for server maintenance such as destroying wild dinos and sending announcements.
- Discord integration for sending server logs and update messages.
- Customizable server settings through `config.yml`.

## Installation

### Using Miniconda

1. Install [Miniconda](https://docs.conda.io/en/latest/miniconda.html) on your server.
2. Clone the repository.
3. Create a new Conda environment using the `environment.yml` file:

    ```bash
    conda env create -f environment.yml
    ```

4. Activate the Conda environment:

    ```bash
    conda activate ark
    ```

### Configuration

- Modify `config/config.yml` to your liking
- You can also create a file at `config/custom.yml` if you wish to override default configurations without altering the original `config.yml`. It will read `config.yml` by default and override anything specified in `custom.yml`.

## Usage

With the "ark" environment activated, navigate to the project root directory and run:

```bash
python src/main.py
```

## Project Structure
- config/: Contains config.yml for server configurations.
- src/: Source code for the server management functionalities.

## Dependencies
The project depends on several Python packages:

- pyyaml: For parsing YAML configuration files.
- requests: For making HTTP requests (used in Discord integration).
- steam[client]: For interacting with Steam client operations.

These are specified in the environment.yml file and will be installed when setting up the Conda environment.

## Contributing
Contributors are welcome to extend the functionality of the program. Please ensure you follow best practices and keep the project structure and coding style consistent.

## License
This project is open-sourced under the MIT License.

## ASA Server
Join our Discord server for support and community discussions. https://discord.gg/BsH25X3pTB
