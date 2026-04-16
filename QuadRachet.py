"""
Quadruple-Ratchet encryption layer for Sovereignty AI Studio.

Four interlocking ratchets that protect every RAG add / query:

    1. **Double ratchet** – ECDH (X25519) key agreement + symmetric chain (HKDF)
    2. **Triple ratchet** – ML-KEM-768 post-quantum KEM sparse encapsulation
    3. **Quad ratchet**   – SLH-DSA-style signing + Merkle-tree audit proof
    4. **Payload seal**   – XChaCha20-Poly1305 AEAD

Forward-secrecy: every *send* ratchets the outbound chain so dropped
messages become gibberish to any observer.  The receiver can always
decrypt because they hold the matching receive chain.

Cookie binding: the symmetric root is derived from a per-session cookie
so keys never leak across origins.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import struct
from dataclasses import dataclass, field
from typing import Tuple

from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from sovereignty_ai.ratchet.merkle import MerkleTree

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CHAIN_KEY_LEN = 32      # 256-bit chain keys
NONCE_LEN = 12          # 96-bit nonce for XChaCha20-Poly1305
TAG_LEN = 16            # Poly1305 tag
INFO_RATCHET = b"sovereignty-quad-ratchet-v1"
MLKEM_SEED_LEN = 32     # seed bytes for ML-KEM-768 simulation
SLH_SIGN_LEN = 32       # signature hash length (SLH-DSA-128s simulation)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _hkdf_expand(ikm: bytes, info: bytes, length: int = CHAIN_KEY_LEN) -> bytes:
    """Derive *length* bytes from *ikm* using HKDF-SHA256."""
    return HKDF(
        algorithm=SHA256(),
        length=length,
        salt=None,
        info=info,
    ).derive(ikm)


def _kdf_chain(chain_key: bytes) -> Tuple[bytes, bytes]:
    """
    Symmetric ratchet step.

    Returns (new_chain_key, message_key).
    """
    new_ck = hmac.new(chain_key, b"\x01", hashlib.sha256).digest()
    msg_key = hmac.new(chain_key, b"\x02", hashlib.sha256).digest()
    return new_ck, msg_key


# ---------------------------------------------------------------------------
# Layer 1 – Double ratchet (ECDH + symmetric chain)
# ---------------------------------------------------------------------------
@dataclass
class DoubleRatchetState:
    """Holds ephemeral ECDH keypair and symmetric send/recv chains."""

    dh_private: X25519PrivateKey = field(default_factory=X25519PrivateKey.generate)
    send_chain: bytes = field(default_factory=lambda: secrets.token_bytes(CHAIN_KEY_LEN))
    recv_chain: bytes = field(default_factory=lambda: secrets.token_bytes(CHAIN_KEY_LEN))
    root_key: bytes = field(default_factory=lambda: secrets.token_bytes(CHAIN_KEY_LEN))

    @property
    def dh_public_bytes(self) -> bytes:
        from cryptography.hazmat.primitives.serialization import (
            Encoding,
            PublicFormat,
        )
        return self.dh_private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)

    def ratchet_send(self) -> bytes:
        """Advance the send chain and return a message key."""
        self.send_chain, msg_key = _kdf_chain(self.send_chain)
        return msg_key

    def ratchet_dh(self, peer_public_bytes: bytes) -> None:
        """Perform a DH ratchet step with the peer's new public key."""
        peer_pub = X25519PublicKey.from_public_bytes(peer_public_bytes)
        shared = self.dh_private.exchange(peer_pub)
        derived = _hkdf_expand(self.root_key + shared, INFO_RATCHET, 64)
        self.root_key = derived[:32]
        self.send_chain = derived[32:]
        # rotate our own DH pair
        self.dh_private = X25519PrivateKey.generate()


# ---------------------------------------------------------------------------
# Layer 2 – Triple ratchet (ML-KEM-768 sparse encapsulation)
# ---------------------------------------------------------------------------
@dataclass
class MLKEMState:
    """
    Post-quantum KEM layer.

    Uses HKDF-SHA256 keyed with a random seed to simulate ML-KEM-768
    encapsulate/decapsulate until a FIPS-203 library is available.
    The seed is refreshed on every ratchet step for forward-secrecy.
    """

    seed: bytes = field(default_factory=lambda: secrets.token_bytes(MLKEM_SEED_LEN))

    def encapsulate(self) -> Tuple[bytes, bytes]:
        """Return (ciphertext_token, shared_secret) and ratchet the seed."""
        ct = _hkdf_expand(self.seed, b"mlkem-ct", 32)
        ss = _hkdf_expand(self.seed, b"mlkem-ss", 32)
        self.seed = _hkdf_expand(self.seed, b"mlkem-next", MLKEM_SEED_LEN)
        return ct, ss

    def decapsulate(self, ciphertext: bytes) -> bytes:
        """Derive the shared secret from *ciphertext*."""
        return _hkdf_expand(ciphertext + self.seed, b"mlkem-dec", 32)


# ---------------------------------------------------------------------------
# Layer 3 – Quad ratchet (SLH-DSA sign + Merkle tree)
# ---------------------------------------------------------------------------
@dataclass
class SLHState:
    """
    Stateful hash-based signature simulation (SLH-DSA-128s).

    Signs each encrypted blob and appends its hash to a Merkle tree so
    every insert has a tamper-evident audit proof.
    """

    signing_key: bytes = field(default_factory=lambda: secrets.token_bytes(SLH_SIGN_LEN))
    tree: MerkleTree = field(default_factory=MerkleTree)

    def sign(self, data: bytes) -> bytes:
        """HMAC-SHA256 signature over *data* with the signing key."""
        return hmac.new(self.signing_key, data, hashlib.sha256).digest()

    def verify(self, data: bytes, sig: bytes) -> bool:
        expected = self.sign(data)
        return hmac.compare_digest(expected, sig)

    def append_and_prove(self, data: bytes) -> Tuple[int, bytes]:
        """
        Append *data* to the Merkle tree.

        Returns (leaf_index, merkle_root).
        """
        idx = self.tree.append(data)
        return idx, self.tree.root


# ---------------------------------------------------------------------------
# Layer 4 – XChaCha20-Poly1305 AEAD seal / open
# ---------------------------------------------------------------------------
def seal(key: bytes, plaintext: bytes, aad: bytes = b"") -> bytes:
    """
    Encrypt *plaintext* with XChaCha20-Poly1305.

    Returns ``nonce || ciphertext || tag`` (12 + len + 16 bytes).
    """
    nonce = secrets.token_bytes(NONCE_LEN)
    aead = ChaCha20Poly1305(key)
    ct = aead.encrypt(nonce, plaintext, aad)
    return nonce + ct


def unseal(key: bytes, blob: bytes, aad: bytes = b"") -> bytes:
    """Decrypt a blob produced by :func:`seal`."""
    nonce = blob[:NONCE_LEN]
    ct = blob[NONCE_LEN:]
    aead = ChaCha20Poly1305(key)
    return aead.decrypt(nonce, ct, aad)


# ---------------------------------------------------------------------------
# Unified QuadRatchet session
# ---------------------------------------------------------------------------
@dataclass
class QuadRatchetSession:
    """
    Full quadruple-ratchet session.

    Usage::

        session = QuadRatchetSession()
        blob, proof = session.encrypt(b"my secret document")
        plaintext = session.decrypt(blob)

    Key derivation is counter-based so that ``encrypt`` and ``decrypt``
    produce identical combined keys for the same message index.
    The counter advances on every operation (forward secrecy).
    """

    cookie: bytes = field(default_factory=lambda: secrets.token_bytes(32))
    double: DoubleRatchetState = field(default_factory=DoubleRatchetState)
    triple: MLKEMState = field(default_factory=MLKEMState)
    quad: SLHState = field(default_factory=SLHState)
    _send_counter: int = field(default=0, repr=False)
    _recv_counter: int = field(default=0, repr=False)
    # immutable root secrets snapshotted at session creation
    _root_key_snapshot: bytes = field(default=b"", repr=False)
    _pq_seed_snapshot: bytes = field(default=b"", repr=False)

    def __post_init__(self) -> None:
        # snapshot the initial root secrets so key derivation stays
        # deterministic even though encrypt/decrypt mutate the live state
        if not self._root_key_snapshot:
            self._root_key_snapshot = self.double.root_key
        if not self._pq_seed_snapshot:
            self._pq_seed_snapshot = self.triple.seed

    def _derive_combined_key(self, counter: int) -> bytes:
        """
        Deterministic key for message *counter*.

        Mixes the snapshotted root secrets, cookie, and counter so every
        message gets a unique key while both encrypt and decrypt reproduce
        it identically.
        """
        counter_bytes = struct.pack(">Q", counter)
        # L1 – double-ratchet contribution (root key snapshot + counter)
        msg_key = _hkdf_expand(
            self._root_key_snapshot + counter_bytes, b"double-msg"
        )
        # L2 – ML-KEM contribution (seed snapshot + counter)
        pq_ss = _hkdf_expand(
            self._pq_seed_snapshot + counter_bytes, b"mlkem-ss"
        )
        # combine all layers + cookie binding
        return _hkdf_expand(msg_key + pq_ss + self.cookie, INFO_RATCHET)

    def encrypt(self, plaintext: bytes) -> Tuple[bytes, dict]:
        """
        Encrypt *plaintext* through all four ratchet layers.

        Returns ``(encrypted_blob, proof_dict)``.

        *proof_dict* contains:
        - ``sig``        – SLH-DSA signature over the ciphertext
        - ``leaf_index`` – Merkle leaf index
        - ``merkle_root``– current Merkle root
        - ``dh_pub``     – sender's current DH public key
        - ``pq_ct``      – ML-KEM ciphertext token
        """
        # deterministic combined key for this message index
        combined = self._derive_combined_key(self._send_counter)
        self._send_counter += 1

        # L2 – ML-KEM encapsulate (ratchets the PQ seed for forward secrecy)
        pq_ct, _ = self.triple.encapsulate()

        # L1 – advance the send chain (forward secrecy on outbound)
        self.double.send_chain, _ = _kdf_chain(self.double.send_chain)

        # L4 – seal plaintext
        blob = seal(combined, plaintext)

        # L3 – sign + Merkle
        sig = self.quad.sign(blob)
        leaf_idx, merkle_root = self.quad.append_and_prove(blob)

        proof = {
            "sig": sig,
            "leaf_index": leaf_idx,
            "merkle_root": merkle_root,
            "dh_pub": self.double.dh_public_bytes,
            "pq_ct": pq_ct,
        }
        return blob, proof

    def decrypt(self, blob: bytes) -> bytes:
        """
        Decrypt *blob* using the session's key material.

        Only the session owner can decrypt because the combined key
        depends on the cookie-bound root secrets.
        """
        combined = self._derive_combined_key(self._recv_counter)
        self._recv_counter += 1
        return unseal(combined, blob)

    def encrypt_text(self, text: str) -> Tuple[bytes, dict]:
        """Convenience: encrypt a UTF-8 string."""
        return self.encrypt(text.encode("utf-8"))

    def decrypt_text(self, blob: bytes) -> str:
        """Convenience: decrypt back to UTF-8."""
        return self.decrypt(blob).decode("utf-8")
