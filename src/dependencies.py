import ctypes
import os
import platform
import shutil
import winreg

import requests

from config import CONFIG
from logger import get_logger
from shell_operations import run_shell_cmd
from steamcmd import check_and_download_steamcmd

logger = get_logger(__name__)


vc_redist_url = CONFIG["advanced"]["download_url"]["vc_redist"]
directx_url = CONFIG["advanced"]["download_url"]["directx"]
AmazonRootCA1_url = CONFIG["advanced"]["download_url"]["AmazonRootCA1"]
r2m02_url = CONFIG["advanced"]["download_url"]["r2m02"]


def install_prerequisites():
    if platform.system() == "Windows":
        install_certificates_windows()
        install_dependencies_windows()
    elif platform.system() == "Linux":
        install_certificates_linux()
        install_dependencies_linux()
    else:
        logger.error("Unsupported operating system.")
    check_and_download_steamcmd()


def install_certificates_windows():
    crypt32 = ctypes.WinDLL("Crypt32.dll")
    store_handle = crypt32.CertOpenSystemStoreW(0, "CA")
    if not store_handle:
        logger.error("Failed to open certificate store")
        return

    try:
        for cert_url in [AmazonRootCA1_url, r2m02_url]:
            cert_content = download_file(cert_url, return_content=True)
            if cert_content:
                # Add certificate to store
                result = crypt32.CertAddEncodedCertificateToStore(
                    ctypes.c_void_p(store_handle),
                    1,  # X509_ASN_ENCODING
                    ctypes.c_char_p(cert_content),
                    ctypes.c_int(len(cert_content)),
                    0,  # CERT_STORE_ADD_REPLACE_EXISTING
                    None,  # Not interested in the added cert's context
                )
                if result == 0:  # 0 indicates failure
                    error_code = ctypes.windll.kernel32.GetLastError()
                    logger.error(f"Failed to add certificate, error code: {error_code}")
                else:
                    logger.info(f"Certificate from {cert_url} installed successfully.")
    except Exception as e:
        logger.error(f"Error installing certificates: {e}")
    finally:
        crypt32.CertCloseStore(store_handle, 0)


def install_certificates_linux():
    # Linux-specific dependency installation logic
    pass


def install_dependencies_windows():
    if not is_dependency_installed(
        winreg.HKEY_LOCAL_MACHINE,
        r"Software\Microsoft\VisualStudio\14.0\VC\Runtimes\x64",
    ):
        install_component(vc_redist_url, "vc_redist.x64.exe", "/passive /norestart")
        logger.info("Visual C++ Redistributable installed successfully.")
    else:
        logger.debug("Visual C++ Redistributable already installed.")

    if not is_dependency_installed(
        winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\DirectX"
    ):
        install_component(directx_url, "dxwebsetup.exe", "/silent")
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


def download_file(url, target_path=None, return_content=False):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Error downloading file: {e}")
        return None

    if return_content:
        return response.content

    if not target_path:
        file_name = url.split("/")[-1]
        target_path = os.path.join(os.environ["TEMP"], file_name)

    with open(target_path, "wb") as file:
        file.write(response.content)

    return target_path
