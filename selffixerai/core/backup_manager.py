"""Backup Manager Module

Handles encrypted backups and retention policies for the self-fixer AI.
Responsible for creating, verifying, and cleaning up old backups.
"""

import fcntl
import gzip
import hashlib
import os
from contextlib import contextmanager
from datetime import datetime

BACKUP_DIR = "backups"
MAX_BACKUPS = 5
BACKUP_CHECKSUM_EXT = ".sha256"
LOCK_FILE = "fixer.lock"


@contextmanager
def filelock(lockpath=LOCK_FILE):
    """Context manager for file-based locking to prevent concurrent writes."""
    fd = os.open(lockpath, os.O_CREAT | os.O_RDWR)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


class BackupManager:
    """Manages encrypted backups and maintains a retention policy."""

    def __init__(self, retention: int = MAX_BACKUPS):
        self.retention = retention
        os.makedirs(BACKUP_DIR, exist_ok=True)

    def _checksum(self, filepath: str) -> str:
        """Compute SHA-256 checksum of a file."""
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()

    def list_backups(self) -> list:
        """List all existing backup files in chronological order."""
        return sorted(
            [
                os.path.join(BACKUP_DIR, f)
                for f in os.listdir(BACKUP_DIR)
                if f.endswith(".patch.gz")
            ]
        )

    def create_backup(self, encrypted: bytes) -> str:
        """Create a new encrypted backup and compute its checksum."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(BACKUP_DIR, f"diff_{timestamp}.patch.gz")
        with filelock(), gzip.open(backup_file, "wb") as f:
            f.write(encrypted)
        checksum_file = backup_file + BACKUP_CHECKSUM_EXT
        with open(checksum_file, "w") as f:
            f.write(self._checksum(backup_file))
        return backup_file

    def verify_backup(self, backup_file: str) -> bool:
        """Verify that the backup's SHA-256 checksum matches the stored value."""
        checksum_file = backup_file + BACKUP_CHECKSUM_EXT
        if not os.path.exists(checksum_file):
            return False
        with open(checksum_file) as f:
            expected = f.read().strip()
        return expected == self._checksum(backup_file)

    def cleanup_old_backups(self) -> None:
        """Delete old backups to enforce the retention policy."""
        backups = self.list_backups()
        if len(backups) > self.retention:
            for old in backups[: len(backups) - self.retention]:
                os.remove(old)
                checksum_file = old + BACKUP_CHECKSUM_EXT
                if os.path.exists(checksum_file):
                    os.remove(checksum_file)
