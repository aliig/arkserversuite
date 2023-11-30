import pytest
from crypto_script import encrypt_data, decrypt_data


def test_encrypt_decrypt():
    original_string = "Test String"
    passphrase = "StrongPassphrase"

    # Encrypt the string
    encrypted_data = encrypt_data(original_string, passphrase)

    # Decrypt the data
    decrypted_string = decrypt_data(encrypted_data, passphrase).decode()

    # Assert that the decrypted string matches the original
    assert decrypted_string == original_string
