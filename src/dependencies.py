import sys
import ctypes
import os
import requests
import subprocess
import zipfile
import winreg

from config import DEFAULT_CONFIG
from steamcmd import STEAMCMD_DIR, is_steam_cmd_installed
from shell_operations import run_shell_cmd

from logger import get_logger

logger = get_logger(__name__)

# check for directx


# check for ark server


def install_certificates():
    amazon_root_ca_url = "https://www.amazontrust.com/repository/AmazonRootCA1.cer"
    certificate_url = "http://crt.r2m02.amazontrust.com/r2m02.cer"
    temp_dir = os.getenv("TEMP", "/tmp")
    amazon_root_ca_path = os.path.join(temp_dir, "AmazonRootCA1.cer")
    certificate_path = os.path.join(temp_dir, "r2m02.cer")

    try:
        # Downloading certificates
        with open(amazon_root_ca_path, "wb") as f:
            f.write(requests.get(amazon_root_ca_url).content)

        with open(certificate_path, "wb") as f:
            f.write(requests.get(certificate_url).content)

        # Here, you would add the logic to install the certificates.
        # This is platform-dependent and may require administrative privileges.

        if sys.platform == "win32":
            # Windows: Use certutil command to install the certificate
            subprocess.run(["certutil", "-addstore", "root", amazon_root_ca_path])
            subprocess.run(["certutil", "-addstore", "root", certificate_path])
        elif sys.platform == "linux":
            # Linux: This varies a lot between distributions.
            # You might need to copy the certificate to /usr/local/share/ca-certificates/
            # and then update the certificates with 'update-ca-certificates' command.
            pass
        elif sys.platform == "darwin":
            # macOS: Use security add-certificates command.
            subprocess.run(
                [
                    "security",
                    "add-certificates",
                    "-k",
                    "/Library/Keychains/System.keychain",
                    amazon_root_ca_path,
                ]
            )
            subprocess.run(
                [
                    "security",
                    "add-certificates",
                    "-k",
                    "/Library/Keychains/System.keychain",
                    certificate_path,
                ]
            )
        else:
            logger.error("Unsupported OS")

    except Exception as e:
        logger.error(f"Error occurred while installing the certificate: {e}")


install_certificates()


steamcmd_url = DEFAULT_CONFIG["download_url"]["steamcmd"]

vc_redist_url = DEFAULT_CONFIG["download_url"]["vc_redist"]
directx_url = DEFAULT_CONFIG["download_url"]["directx"]
certificate_urls = {
    "AmazonRootCA1": DEFAULT_CONFIG["download_url"]["AmazonRootCA1"],
    "r2m02": DEFAULT_CONFIG["download_url"]["r2m02"],
}


def install_server():
    create_directories()
    install_certificates()
    install_dependencies()
    download_and_extract_steamcmd()
    install_ark_server()


def create_directories():
    for directory in [config_data["SteamCMD"], config_data["ARKServerPath"]]:
        if not os.path.exists(directory):
            os.makedirs(directory)


def install_certificates():
    crypt32 = ctypes.WinDLL("Crypt32.dll")
    for cert_name, cert_url in certificate_urls.items():
        cert_content = download_file(cert_url)
        add_certificate_to_store(crypt32, cert_content)
    logger.info(f"Certificate {cert_name} installed successfully.")


def add_certificate_to_store(crypt32, cert_content):
    crypt32.CertAddEncodedCertificateToStore(
        ctypes.c_void_p(crypt32.CertOpenSystemStoreW(0, "CA")),
        1,  # X509_ASN_ENCODING
        ctypes.c_char_p(cert_content),
        ctypes.c_int(len(cert_content)),
        ctypes.c_int(0),  # dwAddDisposition
        ctypes.byref(ctypes.c_int(0)),  # pCertContext
    )


def install_dependencies():
    if not is_dependency_installed(
        winreg.HKEY_LOCAL_MACHINE,
        r"Software\Microsoft\VisualStudio\14.0\VC\Runtimes\x64",
    ):
        install_component(vc_redist_url, "vc_redist.x64.exe", "/passive /norestart")
    else:
        logger.debug("Visual C++ Redistributable already installed.")

    if not is_dependency_installed(
        winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\DirectX"
    ):
        install_component(directx_url, "dxwebsetup.exe", "/silent")
    else:
        logger.debug("DirectX Runtime already installed.")


def is_dependency_installed(key, sub_key):
    try:
        with winreg.OpenKey(key, sub_key):
            return True
    except FileNotFoundError:
        return False


def install_component(url, output_file, arguments):
    component_path = os.path.join(os.environ["TEMP"], output_file)
    download_file(url, component_path)
    run_shell_cmd(f"{component_path} /install {arguments}")


def download_file(url, target_path=None):
    if not target_path:
        file_name = url.split("/")[-1]
        target_path = os.path.join(os.environ["TEMP"], file_name)

    response = requests.get(url, stream=True)
    with open(target_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                file.write(chunk)
    return target_path


def download_and_extract_steamcmd():
    if not is_steam_cmd_installed():
        logger.info("Downloading SteamCMD...")
        steamcmd_zip_path = download_file(steamcmd_url)
        with zipfile.ZipFile(steamcmd_zip_path, "r") as zip_ref:
            zip_ref.extractall(STEAMCMD_DIR)
        os.remove(steamcmd_zip_path)
