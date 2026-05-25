"""Minimal Merkle tree implementation used by QuadRatchetSession."""

from __future__ import annotations

import hashlib
from typing import Iterable


class MerkleTree:
    """Simple append-only Merkle tree over byte leaves."""

    def __init__(self, leaves: Iterable[bytes] | None = None):
        self.leaves: list[bytes] = list(leaves or [])
        self.root: bytes = b""
        self.recompute_root()

    @staticmethod
    def _hash(data: bytes) -> bytes:
        return hashlib.sha256(data).digest()

    def append(self, data: bytes) -> int:
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError("MerkleTree leaves must be bytes-like")
        leaf = bytes(data)
        self.leaves.append(leaf)
        self.recompute_root()
        return len(self.leaves) - 1

    def recompute_root(self) -> bytes:
        level = [self._hash(leaf) for leaf in self.leaves]
        if not level:
            self.root = b""
            return self.root

        while len(level) > 1:
            if len(level) % 2:
                level.append(level[-1])
            level = [self._hash(level[i] + level[i + 1]) for i in range(0, len(level), 2)]

        self.root = level[0]
        return self.root
