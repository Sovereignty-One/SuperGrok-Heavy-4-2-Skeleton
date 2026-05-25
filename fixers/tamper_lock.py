"""Tamper Lock Module

Implements persistent hash chaining + Ed25519 signatures for sovereign
selfcode integrity. Survives restarts and integrates with SCAR audit.
"""

import hashlib
import os
import json
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from ..core.backup_manager import filelock
from fixers.persist_brain import persist_brain

class TamperHardLock:
    STATE_FILE = "chain.state.json"
    MAGIC = b"SGTH"

    def __init__(self, cryptor, backup_mgr, code_file: str = "selfcode.enc", sig_file: str = "chain.sig", key_file: str = "master.key", brain_state: dict = None):
        self.cryptor = cryptor
        self.backup_mgr = backup_mgr
        self.code_file = code_file
        self.sig_file = sig_file
        self.key_file = key_file
        self.brain_state = brain_state or {}
        self.private_key = self._load_or_gen_key()
        self.public_key = self.private_key.public_key()
        self.current_hash, self.signature = self._load_chain_state()

    def _load_or_gen_key(self):
        ed_key_file = self.key_file + ".ed25519"
        if os.path.exists(ed_key_file):
            with open(ed_key_file, "rb") as f:
                return ed25519.Ed25519PrivateKey.from_private_bytes(f.read())
        key = ed25519.Ed25519PrivateKey.generate()
        with open(ed_key_file, "wb") as f:
            f.write(key.private_bytes(encoding=serialization.Encoding.Raw, format=serialization.PrivateFormat.Raw, encryption_algorithm=serialization.NoEncryption()))
        return key

    def _load_chain_state(self):
        if os.path.exists(self.STATE_FILE):
            try:
                with open(self.STATE_FILE, "r") as f:
                    state = json.load(f)
                return state.get("current_hash", ""), bytes.fromhex(state.get("signature", ""))
            except Exception:
                pass
        return "", b""

    def _save_chain_state(self):
        state = {"current_hash": self.current_hash, "signature": self.signature.hex() if self.signature else ""}
        with open(self.STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)

    def sign(self, data: bytes) -> bytes:
        return self.private_key.sign(data)

    def verify(self, data: bytes, sig: bytes) -> bool:
        try:
            self.public_key.verify(sig, data)
            return True
        except Exception:
            return False

    def update_chain(self, new_content: str) -> None:
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
        self._save_chain_state()
        if self.brain_state:
            persist_brain(self.brain_state.get("state", {}), new_logs=[{"type": "tamper_chain_updated", "new_hash": self.current_hash, "timestamp": __import__("time").time()}])

    def is_valid(self) -> bool:
        if not os.path.exists(self.sig_file) or not os.path.exists(self.code_file):
            return False
        with filelock():
            with open(self.sig_file, "rb") as f:
                sig = f.read()
            with open(self.code_file, "rb") as f:
                encrypted = f.read()
        try:
            plaintext = self.cryptor.decrypt(encrypted)
        except Exception:
            return False
        data = (self.current_hash.encode() if self.current_hash else b"") + plaintext.encode()
        return self.verify(data, sig)