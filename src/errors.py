from config import CONFIG
from logger import get_logger

logger = get_logger(__name__)


class ArkServerException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log_error()

    def log_error(self):
        if "install_path" in CONFIG["server"]:
            logger.error(
                f"Check the server log at {CONFIG['server']['install_path']}/ShooterGame/Saved/Logs"
            )


class ArkServerStartError(ArkServerException):
    pass


class ArkServerStopError(ArkServerException):
    pass
