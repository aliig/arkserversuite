import os
import platform
import requests
import ctypes
import winreg
import shutil

from config import DEFAULT_CONFIG
from steamcmd import check_and_download_steamcmd
from shell_operations import run_shell_cmd


from logger import get_logger

logger = get_logger(__name__)


vc_redist_url = DEFAULT_CONFIG["download_url"]["vc_redist"]
directx_url = DEFAULT_CONFIG["download_url"]["directx"]
certificate_urls = {
    "AmazonRootCA1": DEFAULT_CONFIG["download_url"]["AmazonRootCA1"],
    "r2m02": DEFAULT_CONFIG["download_url"]["r2m02"],
}


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
    for cert_name, cert_url in certificate_urls.items():
        cert_content = download_file(cert_url)
        add_certificate_to_store(crypt32, cert_content)
        logger.info(f"Certificate {cert_name} installed successfully.")

def install_certificates_linux():
    for cert_name, cert_url in certificate_urls.items():
        cert_path = download_file(cert_url)
        if cert_path:
            try:
                # This is a common path; it might differ between distributions
                shutil.copy(cert_path, '/usr/local/share/ca-certificates/')
                run_shell_cmd('sudo update-ca-certificates', suppress_output=False)
                logger.info(f"Certificate {cert_name} installed successfully on Linux.")
            except Exception as e:
                logger.error(f"Failed to install certificate {cert_name} on Linux: {e}")

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


def add_certificate_to_store(crypt32, cert_content):
    store_handle = crypt32.CertOpenSystemStoreW(0, "CA")
    if not store_handle:
        logger.error("Failed to open certificate store")
        return

    try:
        crypt32.CertAddEncodedCertificateToStore(
            ctypes.c_void_p(store_handle),
            1,  # X509_ASN_ENCODING
            ctypes.c_char_p(cert_content),
            ctypes.c_int(len(cert_content)),
            ctypes.c_int(0),  # dwAddDisposition
            ctypes.byref(ctypes.c_int(0)),  # pCertContext
        )
    finally:
        crypt32.CertCloseStore(store_handle, 0)


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


def download_file(url, target_path=None):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Error downloading file: {e}")
        return None

    if not target_path:
        file_name = url.split("/")[-1]
        target_path = os.path.join(os.environ["TEMP"], file_name)

    with open(target_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                file.write(chunk)
    return target_path