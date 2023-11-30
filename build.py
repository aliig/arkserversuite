import subprocess
import os
import shutil
import subprocess
import base64
import secrets
import tempfile
import zipfile
import stat
import fnmatch

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


def run_command(command, cwd=None):
    subprocess.run(command, shell=True, check=True, cwd=cwd)


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

    # Define paths for --add-data
    ps_source = os.path.join(src_dir_temp, "ps")
    ps_dest = "ps"
    key_source = os.path.join(temp_dir, "encrypted_key.enc")
    key_dest = "."
    passphrase_source = os.path.join(temp_dir, "passphrase.txt")
    passphrase_dest = "."

    # Build executable with PyInstaller
    pyinstaller_command = (
        f"pyinstaller --onefile --name=arkserversuite "
        f'--add-data "{ps_source};{ps_dest}" '
        f'--add-data "{key_source};{key_dest}" '
        f'--add-data "{passphrase_source};{passphrase_dest}" '
        f"\"{os.path.join(src_dir_temp, 'main.py')}\""
    )

    print(f"Running command: {pyinstaller_command}")
    run_command(pyinstaller_command, cwd=src_dir_temp)

    # Move the executable to the dist directory
    dist_dir_temp = os.path.join(temp_dir, "dist")
    if not os.path.exists(dist_dir_temp):
        os.makedirs(dist_dir_temp)
    # built_exe_path = os.path.join(src_dir_temp, "dist", "arkserversuite.exe")
    # shutil.move(built_exe_path, os.path.join(dist_dir_temp, "arkserversuite.exe"))


def read_gitignore_patterns():
    gitignore_path = os.path.join(project_dir, ".gitignore")
    patterns = []
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as file:
            for line in file:
                stripped_line = line.strip()
                if stripped_line and not stripped_line.startswith("#"):
                    patterns.append(stripped_line)
    return patterns


def should_exclude(file, exclude_patterns):
    return any(fnmatch.fnmatch(file, pattern) for pattern in exclude_patterns)


def zip_artifacts():
    exclude_patterns = read_gitignore_patterns()

    exe_path = os.path.join(temp_dir, "src", "dist", "arkserversuite.exe")
    config_path = os.path.join(temp_dir, "config")
    zip_path = os.path.join(temp_dir, "release.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(exe_path, os.path.basename(exe_path))
        for folder, subfolders, files in os.walk(config_path):
            for file in files:
                file_path = os.path.join(folder, file)
                relative_path = os.path.relpath(file_path, temp_dir)
                if not should_exclude(relative_path, exclude_patterns):
                    zipf.write(file_path, relative_path)

    print(f"Artifacts zipped and moved to dist directory.")


def onerror(func, path, exc_info):
    if not os.access(path, os.W_OK):
        # Is the error an access error ?
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise


def main():
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir, onerror=onerror)

    # Copy source to temporary directory
    shutil.copytree(project_dir, temp_dir, dirs_exist_ok=True)

    # Change the current working directory to the temporary directory
    os.chdir(temp_dir)

    # Call the rest of your build functions
    perform_encryption()
    build_executable()
    zip_artifacts()

    # Copy the final artifacts back to the dist directory
    # shutil.copytree(os.path.join(temp_dir, "dist"), dist_dir, dirs_exist_ok=True)
    os.makedirs(dist_dir, exist_ok=True)
    shutil.copy(
        os.path.join(temp_dir, "release.zip"), os.path.join(dist_dir, "release.zip")
    )

    try:
        shutil.rmtree(temp_dir, onerror=onerror)
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
