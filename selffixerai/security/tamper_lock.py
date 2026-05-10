"""Tamper Lock Module

Implements hash chaining and Ed25519 signatures to detect unauthorized
code modifications.
"""

import hashlib
import os

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from ..core.backup_manager import filelock


class TamperHardLock:
    """Manages tamper detection using signature verification and hash-chaining."""

    def __init__(
        self,
        cryptor,
        backup_mgr,
        code_file: str = "selfcode.enc",
        sig_file: str = "chain.sig",
        key_file: str = "master.key",
    ):
        self.cryptor = cryptor
        self.backup_mgr = backup_mgr
        self.code_file = code_file
        self.sig_file = sig_file
        self.key_file = key_file
        self.private_key = self._load_or_gen_key()
        self.public_key = self.private_key.public_key()
        self.current_hash = ""
        self.signature = b""

    def _load_or_gen_key(self):
        """Load an existing Ed25519 private key or generate a new one."""
        ed_key_file = self.key_file + ".ed25519"
        if os.path.exists(ed_key_file):
            with open(ed_key_file, "rb") as f:
                return ed25519.Ed25519PrivateKey.from_private_bytes(f.read())
        key = ed25519.Ed25519PrivateKey.generate()
        with open(ed_key_file, "wb") as f:
            f.write(
                key.private_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PrivateFormat.Raw,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )
        return key

    def sign(self, data: bytes) -> bytes:
        """Sign data with the Ed25519 private key."""
        return self.private_key.sign(data)

    def verify(self, data: bytes, sig: bytes) -> bool:
        """Verify an Ed25519 signature against data."""
        try:
            self.public_key.verify(sig, data)
            return True
        except Exception:
            return False

    def update_chain(self, new_content: str) -> None:
        """Append new_content to the hash chain, sign, encrypt, and persist."""
        prev = self.current_hash.encode() if self.current_hash else b""
        data = prev + new_content.encode()
        self.current_hash = hashlib.blake2b(data, digest_size=32).hexdigest()
        self.signature = self.sign(data)

        encrypted = self.cryptor.encrypt(new_content)
        with filelock():
            self.backup_mgr.create_backup(encrypted)
            self.backup_mgr.cleanup_old_backups()
            with open(self.sig_file, "wb") as f:
                f.write(self.signature)
            with open(self.code_file, "wb") as f:
                f.write(encrypted)

    def is_valid(self, content: str) -> bool:
        """Return True if the current signature matches content."""
        if not os.path.exists(self.sig_file):
            return False
        with filelock():
            with open(self.sig_file, "rb") as f:
                sig = f.read()
        data = (self.current_hash.encode() if self.current_hash else b"") + content.encode()
        return self.verify(data, sig)
