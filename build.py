import subprocess
import os
import shutil
import subprocess
import base64
import secrets
import tempfile

from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Define paths and environment names
project_dir = os.path.dirname(os.path.realpath(__file__))
src_dir = os.path.join(project_dir, "src")
dist_dir = os.path.join(project_dir, "dist")
temp_dir = tempfile.mkdtemp(prefix="build_")  # Create a temporary directory

curseforge_api_key = os.getenv("CURSEFORGE_API_KEY")

if not curseforge_api_key:
    raise Exception("CURSEFORGE_API_KEY must be set in .env file")


def run_command(command):
    subprocess.run(command, shell=True, check=True)


def generate_passphrase():
    # Generate a 32-byte random string and encode it in Base64
    random_bytes = secrets.token_bytes(32)
    passphrase = base64.b64encode(random_bytes).decode("utf-8")
    return passphrase


def perform_encryption():
    passphrase = generate_passphrase()

    # Define paths in the temporary directory
    script_path = os.path.join(temp_dir, "src", "crypto_script.py")
    output_path = os.path.join(temp_dir, "encrypted_key.enc")
    passphrase_path = os.path.join(temp_dir, "passphrase.txt")

    # Run the encryption script
    run_command(
        f"python {script_path} --mode encrypt --input {curseforge_api_key} --output {output_path} --passphrase {passphrase}"
    )

    # Save the passphrase to a file in the temporary directory
    with open(passphrase_path, "w") as file:
        file.write(passphrase)

    print("Encryption completed.")


def build_executable():
    # Prepare the source directory
    src_dir_temp = os.path.join(temp_dir, "src")
    init_py_path = os.path.join(src_dir_temp, "__init__.py")
    if os.path.exists(init_py_path):
        os.remove(init_py_path)

    # Build executable with PyInstaller
    pyinstaller_command = (
        f"pyinstaller --onefile --name=arkserversuite "
        f"--add-data '{os.path.join(src_dir_temp, 'ps;ps')}' "
        f"--add-data '{os.path.join(temp_dir, 'encrypted_key.enc')};.' "
        f"--add-data '{os.path.join(temp_dir, 'passphrase.txt')};.' "
        f"{os.path.join(src_dir_temp, 'main.py')}"
    )
    run_command(pyinstaller_command, cwd=src_dir_temp)

    # Move the executable to the dist directory
    dist_dir_temp = os.path.join(temp_dir, "dist")
    if not os.path.exists(dist_dir_temp):
        os.makedirs(dist_dir_temp)
    built_exe_path = os.path.join(src_dir_temp, "dist", "arkserversuite.exe")
    shutil.move(built_exe_path, os.path.join(dist_dir_temp, "arkserversuite.exe"))


def zip_artifacts():
    # Define paths
    exe_path = os.path.join(temp_dir, "dist", "arkserversuite.exe")
    config_path = os.path.join(temp_dir, "config")
    zip_path = os.path.join(temp_dir, "release.zip")

    # Zip the executable and config directory
    zip_command = f"7z a {zip_path} {exe_path} {config_path}"
    run_command(zip_command)

    # Move the zip file back to the original dist directory in the project
    if not os.path.exists(dist_dir):
        os.makedirs(dist_dir)
    shutil.move(zip_path, os.path.join(dist_dir, "release.zip"))

    print("Artifacts zipped and moved to dist directory.")


def main():
    # Copy source to temporary directory
    shutil.copytree(project_dir, temp_dir, dirs_exist_ok=True)

    # Change the current working directory to the temporary directory
    os.chdir(temp_dir)

    # Call the rest of your build functions
    perform_encryption()
    build_executable()
    zip_artifacts()

    # Copy the final artifacts back to the dist directory
    shutil.copytree(os.path.join(temp_dir, "dist"), dist_dir, dirs_exist_ok=True)

    # Optionally, clean up the temporary directory
    shutil.rmtree(temp_dir)


if __name__ == "__main__":
    main()
