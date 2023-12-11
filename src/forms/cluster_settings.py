import datetime
import ipaddress

from utils.networking import get_internal_ip

from .base import FieldType, FormField

CLUSTER_SETTINGS = [
    FormField(
        field_name="Private IP address",
        field_type=FieldType.TEXT,
        required=True,
        default_value=get_internal_ip(),
        tooltip="The internal IP address of the server.",
        validation_func=lambda x: isinstance(
            ipaddress.ip_address(x), ipaddress.IPv4Address
        )
        or isinstance(ipaddress.ip_address(x), ipaddress.IPv6Address),
    ),
    FormField(
        field_name="Timezone",
        field_type=FieldType.TEXT,
        required=True,
        default_value=datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo,
        tooltip="The timezone of the server.",
    ),
]
"""
server:
  name: "MyArkServer" # The name of your ARK server
  ip_address: "192.168.1.42" # The internal IP address where your ARK server is hosted
  install_path: "C:\\gameservers\\ark_survival_ascended" # The file path where your ARK server files are installed
  port: 7777 # The main port for your ARK server
  query_port: 27015
  rcon_port: 32330
  max_players: 26 # The maximum number of players that can join the server
  password: "password" # Server password for private access (if needed)
  map: "TheIsland_WP" # The map that the server will load
  admin_password: "password2" # Password for admin privileges
  timezone: "America/New_York" # The timezone your server's operating system is set to
  admin_list: # optional list of OSS IDs for server admins, check with `whoami` or `cheat listplayers`
    # - "12345678901234567"
  use_server_api: True # set to True to use the Ark Server API to enable plugins. https://gameservershub.com/forums/resources/ark-survival-ascended-serverapi-crossplay-supported.683/
"""
