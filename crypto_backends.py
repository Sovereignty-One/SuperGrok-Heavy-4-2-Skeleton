import logging
import sys
from typing import Callable, Dict, Tuple

logger = logging.getLogger("crypto_backends")
logger.setLevel(logging.DEBUG)


def iosenclave_ed25519_x25519_sign(payload: bytes) -> Tuple[bytes, bytes, bytes]:
    """Platform stub for iOS/macOS Secure Enclave Ed25519 + X25519 signing."""
    raise NotImplementedError("iOS Secure Enclave signing backend is not configured")


def androidkeystore_ed25519_x25519_sign(payload: bytes) -> Tuple[bytes, bytes, bytes]:
    """Platform stub for Android Keystore Ed25519 + X25519 signing."""
    raise NotImplementedError("Android Keystore signing backend is not configured")


def tpm_ed25519_x25519_sign(payload: bytes) -> Tuple[bytes, bytes, bytes]:
    """Platform stub for TPM 2.0 Ed25519 + X25519 signing."""
    raise NotImplementedError("TPM signing backend is not configured")


def iossecureenclave_sign(payload: bytes) -> Tuple[bytes, bytes, bytes]:
    """Sign payload via iOS/macOS Secure Enclave."""
    return iosenclave_ed25519_x25519_sign(payload)


def androidkeystoresign(payload: bytes) -> Tuple[bytes, bytes, bytes]:
    """Sign payload via Android Keystore (Titan)."""
    return androidkeystore_ed25519_x25519_sign(payload)


def tpmed25519x25519_sign(payload: bytes) -> Tuple[bytes, bytes, bytes]:
    """Sign payload via TPM 2.0 (Windows/Linux)."""
    return tpm_ed25519_x25519_sign(payload)


PLATFORM_SIGNERS: Dict[str, Callable[[bytes], Tuple[bytes, bytes, bytes]]] = {
    "ios": iossecureenclave_sign,
    "darwin": iossecureenclave_sign,
    "android": androidkeystoresign,
    "linux": tpmed25519x25519_sign,
    "win": tpmed25519x25519_sign,
}


def getplatformsigner() -> Callable[[bytes], Tuple[bytes, bytes, bytes]]:
    """Detect platform and return the correct signer function from the dispatcher."""
    plat = sys.platform.lower()
    logger.debug("Detected platform: %s", plat)

    for key, signer in PLATFORM_SIGNERS.items():
        if key in plat:
            logger.debug("Using signer for platform key: %s", key)
            return signer

    logger.error("Unsupported platform: %s", plat)
    raise RuntimeError(f"Unsupported platform for hardware seal: {plat}")


def get_platform_signer() -> Callable[[bytes], Tuple[bytes, bytes, bytes]]:
    """PEP 8 alias for getplatformsigner."""
    return getplatformsigner()
