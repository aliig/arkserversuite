import socket
import struct

import requests


def get_public_ip() -> str | None:
    """
    Fetches the public IP address of the user.

    :return: The public IP address as a string, or None if the network is unreachable.
    """
    try:
        response = requests.get("https://api.ipify.org")
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return None


def get_internal_ip() -> str | None:
    """
    Fetches the internal IP address of the user.

    :return: The internal IP address as a string, or None if not available.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Connect to an external address to determine the internal IP
        s.connect(("8.8.8.8", 80))
        internal_ip = s.getsockname()[0]
        s.close()
        return internal_ip
    except socket.error:
        return None


def is_connected_to_internet(
    host: str = "8.8.8.8", port: int = 53, timeout: int = 3
) -> bool:
    """
    Checks if the system is connected to the internet.

    :param host: A remote host to test the connection against, default is Google's DNS server.
    :param port: The port to use for the connection, default is 53 (DNS).
    :param timeout: Connection timeout in seconds.
    :return: True if connected to the internet, False otherwise.
    """
    try:
        # Use socket to attempt to connect to an external host
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def check_port_forwarding(public_ip: str, port: int) -> str:
    """
    Check if a port is being forwarded using yougetsignal.com.
      -->> unfortunately only seems to work for RCON port for ASA?

    :param public_ip: The public IP address of the network.
    :param port: The port number to check.
    :return: A string indicating if the port is open or not.
    """
    url = "https://ports.yougetsignal.com/check-port.php"
    data = {"remoteAddress": public_ip, "portNumber": port}
    headers = {"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest"}

    response = requests.post(url, data=data, headers=headers)
    if response.status_code == 200:
        return "is open" in response.text
    else:
        return "Error: Unable to check port status."


if __name__ == "__main__":
    port = 32330
    print(public_ip := get_public_ip())
    print(check_port_forwarding(public_ip, port))
