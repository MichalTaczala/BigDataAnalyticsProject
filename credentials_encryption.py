"""Code generated using Claude 3.5 Sonnet"""
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import yaml


class YAMLCredentialsHandler:
    # Fixed file paths
    ENCRYPTED_FILE = "credentials_encrypted.yaml"
    DECRYPTED_FILE = "credentials.yaml"

    def __init__(self, master_password):
        """Initialize with a master password that will be used for encryption/decryption"""
        # Generate a key from the master password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'<9m!ivc_x-lc`ZxoaF0A<D-EH)gkAwB6q)tV|r>qa$ 875Cl:k{rGxb2hS9mxwn2',
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
        self.cipher_suite = Fernet(key)

    def encrypt_credentials(self):
        """
        Encrypt credentials from YAML file and save to encrypted file
        """
        try:
            # Read the YAML file
            with open(self.DECRYPTED_FILE, 'r') as f:
                credentials = yaml.safe_load(f)

            # Convert to YAML string and encrypt
            credentials_str = yaml.dump(credentials, default_flow_style=False)
            encrypted_data = self.cipher_suite.encrypt(credentials_str.encode())

            # Save encrypted data to file
            with open(self.ENCRYPTED_FILE, 'wb') as f:
                f.write(encrypted_data)

            print(f"Credentials encrypted and saved to {self.ENCRYPTED_FILE}")

        except Exception as e:
            print(f"Error encrypting credentials: {str(e)}")
            raise

    def decrypt_credentials(self):
        """
        Decrypt credentials from encrypted file and save to YAML file
        """
        try:
            # Read the encrypted file
            with open(self.ENCRYPTED_FILE, 'rb') as f:
                encrypted_data = f.read()

            # Decrypt the data
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)

            # Parse YAML and save to file
            credentials = yaml.safe_load(decrypted_data.decode())
            with open(self.DECRYPTED_FILE, 'w') as f:
                yaml.dump(credentials, f, default_flow_style=False)

            print(f"Credentials decrypted and saved to {self.DECRYPTED_FILE}")

        except Exception as e:
            print(f"Error decrypting credentials: {str(e)}")
            raise


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Encrypt or decrypt YAML credentials file')
    parser.add_argument('action', choices=['encrypt', 'decrypt'], help='Action to perform')
    parser.add_argument('--password', help='Master password (alternatively, use MASTER_PASSWORD env var)')

    args = parser.parse_args()

    # Get master password from argument or environment variable
    master_password = args.password
    if not master_password:
        raise ValueError("Master password")

    handler = YAMLCredentialsHandler(master_password)

    if args.action == 'encrypt':
        handler.encrypt_credentials()
    else:
        handler.decrypt_credentials()


if __name__ == "__main__":
    main()
