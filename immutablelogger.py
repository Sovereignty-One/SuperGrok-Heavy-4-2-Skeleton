#!/usr/bin/env python3
"""
Immutable Logger — Append-only JSON logger with digital signature and integrity verification.
"""
import json
import os
import hashlib
import time


class ImmutableLogger:
    """Append-only JSON logger with digital signature and integrity verification."""

    def __init__(self, logfile: str, secret_key: str = "STRICTSECRETKEY"):
        self.log_file = logfile
        self.secret_key = secret_key
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', encoding='utf-8') as f:
                pass

    def _sign(self, data: dict) -> str:
        payload = json.dumps(data, sort_keys=True)
        return hashlib.sha256((payload + self.secret_key).encode()).hexdigest()

    def append_log(self, data: dict):
        timestamp = time.time()
        data["timestamp"] = timestamp
        data["signature"] = self._sign(data)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            json.dump(data, f)
            f.write('\n')

    def verify_integrity(self) -> bool:
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    entry = json.loads(line)
                    signature = entry.pop("signature", None)
                    expected = self._sign(entry)
                    if signature != expected:
                        return False
            return True
        except Exception:
            return False

    def write_boot_entry(self, system_id: str, chain_seed: str = ""):
        entry = {
            "event": "BOOT",
            "system_id": system_id,
            "chain_seed": chain_seed,
            "status": "BOOT_OK"
        }
        self.append_log(entry)
        return self.verify_integrity()

    def file_checksum(self) -> str:
        sha = hashlib.sha256()
        with open(self.log_file, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha.update(chunk)
        return sha.hexdigest()
