import base64
import os
import argparse
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend


def derive_key(passphrase, salt=None):
    """Derives a key using the given passphrase and salt."""
    if salt is None:
        salt = os.urandom(16)  # Generate a new salt for encryption
    # Key Derivation Function
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend(),
    )
    key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))
    return key, salt


def encrypt_data(data, passphrase):
    key, salt = derive_key(passphrase)
    cipher_suite = Fernet(key)
    encrypted_data = cipher_suite.encrypt(data.encode())
    return salt + encrypted_data  # Prepend salt to encrypted data


def decrypt_data(encrypted_data_with_salt, passphrase):
    salt = encrypted_data_with_salt[:16]  # Extract the salt
    encrypted_data = encrypted_data_with_salt[16:]
    key, _ = derive_key(passphrase, salt)
    cipher_suite = Fernet(key)
    return cipher_suite.decrypt(encrypted_data)


def main():
    parser = argparse.ArgumentParser(description="Encrypt/Decrypt data.")
    parser.add_argument(
        "--mode",
        choices=["encrypt", "decrypt"],
        required=True,
        help="Operation mode: encrypt or decrypt",
    )
    parser.add_argument(
        "--input", required=True, help="Input data to encrypt or path to input file"
    )
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument(
        "--passphrase", required=True, help="Passphrase for encryption/decryption"
    )

    args = parser.parse_args()

    if args.mode == "encrypt":
        try:
            # Attempt to open the input as a file
            with open(args.input, "r") as file:
                data = file.read()
        except FileNotFoundError:
            # If file not found, treat input as a raw string
            data = args.input

        encrypted_data = encrypt_data(data, args.passphrase)
        with open(args.output, "wb") as file:
            file.write(encrypted_data)

    elif args.mode == "decrypt":
        with open(args.input, "rb") as file:
            encrypted_data_with_salt = file.read()
        decrypted_data = decrypt_data(encrypted_data_with_salt, args.passphrase)
        with open(args.output, "wb") as file:
            file.write(decrypted_data)


if __name__ == "__main__":
    main()
