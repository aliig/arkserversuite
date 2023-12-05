import os
import platform
import shutil
import winreg

from config import CONFIG
from logger import get_logger
from shell_operations import run_shell_cmd
from steamcmd import check_and_download_steamcmd
from utils import resource_path, download_file

logger = get_logger(__name__)


VC_REDIST_URL = CONFIG["advanced"]["download_url"]["vc_redist"]
DIRECTX_URL = CONFIG["advanced"]["download_url"]["directx"]
CERTIFICATE_URLS = {
    "AmazonRootCA1": CONFIG["advanced"]["download_url"]["AmazonRootCA1"],
    "r2m02": CONFIG["advanced"]["download_url"]["r2m02"],
}


def install_certificates():
    if platform.system() == "Windows":
        install_certificates_windows()
    elif platform.system() == "Linux":
        install_certificates_linux()
    else:
        logger.error("Unsupported operating system.")


def install_prerequisites():
    if platform.system() == "Windows":
        install_dependencies_windows()
    elif platform.system() == "Linux":
        install_dependencies_linux()
    else:
        logger.error("Unsupported operating system.")
    check_and_download_steamcmd()


def check_certificate_windows() -> bool:
    script_path = resource_path(os.path.join("ps", "check_certificates_windows.ps1"))

    all_certificates_installed = True

    for cert_name, cert_url in CERTIFICATE_URLS.items():
        cmd = f'powershell -ExecutionPolicy Bypass -File "{script_path}" -certUrl "{cert_url}"'

        try:
            process = run_shell_cmd(cmd, suppress_output=True)
            if process.returncode == 0:
                if "Exists" in process.stdout:
                    logger.debug(f"Certificate {cert_name} already exists.")
                elif "NotInstalled" in process.stdout:
                    logger.debug(f"Certificate {cert_name} is not installed.")
                    all_certificates_installed = False
                else:
                    logger.error(
                        f"Unknown response while checking certificate {cert_name} using PowerShell."
                    )
            else:
                logger.error(
                    f"Failed to check certificate {cert_name} using PowerShell."
                )
        except Exception as e:
            logger.error(
                f"Exception occurred while checking certificate {cert_name} using PowerShell: {e}"
            )

    return all_certificates_installed


def install_certificates_windows():
    script_path = resource_path(os.path.join("ps", "install_certificates_windows.ps1"))
    logger.debug(f"PowerShell script path for installing certificates: {script_path}")

    for cert_name, cert_url in CERTIFICATE_URLS.items():
        cmd = f'powershell -ExecutionPolicy Bypass -File "{script_path}" -certUrl "{cert_url}" -certName "{cert_name}"'

        try:
            process = run_shell_cmd(cmd, suppress_output=True)
            if process.returncode == 0:
                if "Installed" in process.stdout:
                    logger.info(
                        f"Certificate {cert_name} installed successfully using PowerShell."
                    )
                elif "Exists" in process.stdout:
                    logger.debug(f"Certificate {cert_name} already exists.")
                else:
                    logger.error(
                        f"Unknown response while installing certificate {cert_name} using PowerShell."
                    )
            else:
                logger.error(
                    f"Failed to install certificate {cert_name} using PowerShell."
                )
        except Exception as e:
            logger.error(
                f"Exception occurred while installing certificate {cert_name} using PowerShell: {e}"
            )


def install_certificates_linux():
    for cert_name, cert_url in CERTIFICATE_URLS.items():
        cert_path = download_file(cert_url)
        if cert_path:
            try:
                # This is a common path; it might differ between distributions
                shutil.copy(cert_path, "/usr/local/share/ca-certificates/")
                run_shell_cmd("sudo update-ca-certificates", suppress_output=False)
                logger.info(f"Certificate {cert_name} installed successfully on Linux.")
            except Exception as e:
                logger.error(f"Failed to install certificate {cert_name} on Linux: {e}")


def install_dependencies_windows():
    # VS Studio
    if not is_dependency_installed(
        winreg.HKEY_LOCAL_MACHINE,
        r"Software\Microsoft\VisualStudio\14.0\VC\Runtimes\x64",
    ):
        install_component(VC_REDIST_URL, "vc_redist.x64.exe", "/passive /norestart")
        logger.info("Visual C++ Redistributable installed successfully.")
    else:
        logger.debug("Visual C++ Redistributable already installed.")

    # DirectX
    if not is_dependency_installed(
        winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\DirectX"
    ):
        install_component(DIRECTX_URL, "dxwebsetup.exe", "/silent")
        logger.info("DirectX Runtime installed successfully.")
    else:
        logger.debug("DirectX Runtime already installed.")


def install_dependencies_linux():
    # Linux-specific dependency installation logic
    pass


def is_dependency_installed(key, sub_key):
    try:
        with winreg.OpenKey(key, sub_key):
            return True
    except FileNotFoundError:
        return False


def install_component(url, output_file, arguments):
    component_path = os.path.join(os.environ["TEMP"], output_file)
    download_file(url, component_path)
    try:
        run_shell_cmd(f"{component_path} /install {arguments}")
    finally:
        try:
            os.remove(component_path)
            logger.debug(f"Temporary file {component_path} deleted.")
        except OSError as e:
            logger.warning(f"Could not delete temporary file {component_path}: {e}")
