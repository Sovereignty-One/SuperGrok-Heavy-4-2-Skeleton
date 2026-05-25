"""Encryption Module

Provides ChaCha20Poly1305-based encryption and decryption for self-fixer
code files with proper key management and integrity binding.
"""

import os
import stat
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.exceptions import InvalidTag

class CodeCryptor:
    MAGIC = b"SGCR"
    VERSION = 1
    NONCE_SIZE = 12
    KEY_SIZE = 32

    def __init__(self, key_file: str = "master.key"):
        self.key_file = key_file
        self._load_or_create_key()

    def _load_or_create_key(self):
        if os.path.exists(self.key_file):
            with open(self.key_file, "rb") as f:
                key = f.read()
            if len(key) != self.KEY_SIZE:
                raise ValueError(f"Invalid key length in {self.key_file}. Expected {self.KEY_SIZE} bytes.")
        else:
            key = ChaCha20Poly1305.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(key)
            os.chmod(self.key_file, stat.S_IRUSR | stat.S_IWUSR)
        self.key = key
        self.cipher = ChaCha20Poly1305(self.key)

    def encrypt(self, content: str, filename: str = "unknown") -> bytes:
        if not isinstance(content, str):
            raise TypeError("content must be a string")
        nonce = os.urandom(self.NONCE_SIZE)
        aad = f"{self.MAGIC.decode()}-v{self.VERSION}-{filename}".encode()
        ciphertext = self.cipher.encrypt(nonce, content.encode(), aad)
        return self.MAGIC + bytes([self.VERSION]) + nonce + ciphertext

    def decrypt(self, blob: bytes) -> str:
        if len(blob) < 5 + self.NONCE_SIZE:
            raise ValueError("Blob too short to be valid encrypted data")
        magic = blob[:4]
        version = blob[4]
        nonce = blob[5:5 + self.NONCE_SIZE]
        ciphertext = blob[5 + self.NONCE_SIZE:]
        if magic != self.MAGIC or version != self.VERSION:
            raise ValueError("Invalid magic or version — wrong key or corrupted file")
        aad = f"{self.MAGIC.decode()}-v{self.VERSION}-unknown".encode()
        try:
            plaintext = self.cipher.decrypt(nonce, ciphertext, aad)
            return plaintext.decode()
        except InvalidTag:
            raise ValueError("Decryption failed — data may be tampered or key is wrong")

    def rotate_key(self, new_key_file: str = "master.key.new"):
        new_key = ChaCha20Poly1305.generate_key()
        with open(new_key_file, "wb") as f:
            f.write(new_key)
        os.chmod(new_key_file, stat.S_IRUSR | stat.S_IWUSR)
        print(f"New key generated at {new_key_file}. Manual re-encryption of files required.")