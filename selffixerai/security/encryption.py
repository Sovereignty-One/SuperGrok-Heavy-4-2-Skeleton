"""Encryption Module

Provides ChaCha20Poly1305-based encryption and decryption for self-fixer
code files.
"""

import os

from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305


class CodeCryptor:
    """Encrypts and decrypts code using ChaCha20-Poly1305 AEAD cipher."""

    def __init__(self, key_file: str = "master.key"):
        self.key_file = key_file
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                key = f.read()
        else:
            key = ChaCha20Poly1305.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
        self.key = key
        self.cipher = ChaCha20Poly1305(self.key)

    def encrypt(self, content: str) -> bytes:
        """Encrypt the provided string into bytes."""
        nonce = os.urandom(12)
        ciphertext = self.cipher.encrypt(nonce, content.encode(), None)
        return nonce + ciphertext

    def decrypt(self, blob: bytes) -> str:
        """Decrypt bytes to the original string."""
        nonce, ciphertext = blob[:12], blob[12:]
        return self.cipher.decrypt(nonce, ciphertext, None).decode()
