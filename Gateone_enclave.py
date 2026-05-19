from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import os
import time
import logging
import oqs
from gateone_enclave.tpm_attestation import verify_tpm_quote

app = FastAPI(title="GATEONE PQC Verifier")
SIG_ALG = "ML-DSA-65"
logger = logging.getLogger(__name__)

# Persist signing keys so process restarts do not regenerate them.
KEY_DIR = os.path.join(os.path.expanduser("~"), ".gateone")
PUBLIC_KEY_FILE = os.path.join(KEY_DIR, "ml_dsa_65_public.key")
PRIVATE_KEY_FILE = os.path.join(KEY_DIR, "ml_dsa_65_private.key")


def _load_or_generate_signing_keys():
    try:
        if os.path.isfile(PUBLIC_KEY_FILE) and os.path.isfile(PRIVATE_KEY_FILE):
            with open(PUBLIC_KEY_FILE, "rb") as pub_file:
                public_key = pub_file.read()
            with open(PRIVATE_KEY_FILE, "rb") as priv_file:
                private_key = priv_file.read()
            if public_key and private_key:
                return public_key, private_key
    except OSError:
        # If persisted keys cannot be read (missing/corrupt/permission issue),
        # intentionally fall back to generating a fresh keypair below.
        pass

    signer = oqs.Signature(SIG_ALG)
    public_key = signer.generate_keypair()
    private_key = signer.export_secret_key()
    try:
        os.makedirs(KEY_DIR, exist_ok=True)
        with open(PUBLIC_KEY_FILE, "wb") as pub_file:
            pub_file.write(public_key)
        private_fd = os.open(PRIVATE_KEY_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(private_fd, "wb") as priv_file:
            priv_file.write(private_key)
    except OSError:
        # If keys cannot be persisted (read-only home, permission issue, etc.),
        # keep the freshly generated keypair in memory and let startup continue.
        pass
    return public_key, private_key


def get_signing_keys():
    """Load persisted signing keys or generate them lazily when needed."""
    return _load_or_generate_signing_keys()

class AttestationToken(BaseModel):
    attestation_token: str
    max_age_seconds: int = 300

@app.post("/verify-attestation")
async def verify_attestation(token: AttestationToken):
    try:
        data = json.loads(token.attestation_token)
        payload = data.get("payload", {})
        signature_hex = data.get("signature", "")
        public_key_hex = data.get("public_key", "")
        tpm_quote = data.get("tpm_quote",)

        # Freshness check
        age = time.time() - payload.get("timestamp", 0)
        if age > token.max_age_seconds:
            return {"valid": False, "reason": "token_too_old"}

        # Real Dilithium verification
        message_bytes = json.dumps(payload, sort_keys=True).encode()
        signature = bytes.fromhex(signature_hex)
        public_key = bytes.fromhex(public_key_hex)
        
        verifier = oqs.Signature(SIG_ALG)
        is_dilithium_valid = verifier.verify(message_bytes, signature, public_key)

        # Real TPM 2.0 verification
        is_tpm_valid = verify_tpm_quote(tpm_quote, payload.get("nonce", ""))

        if is_dilithium_valid and is_tpm_valid:
            return {
                "valid": True,
                "node_id": payload.get("node_id"),
                "algorithm": "ML-DSA-65 + TPM 2.0"
            }
        else:
            return {
                "valid": False,
                "dilithium_valid": is_dilithium_valid,
                "tpm_valid": is_tpm_valid
            }

    except Exception as e:
        logger.exception("Attestation verification failed")
        return {"valid": False, "reason": "internal_verification_error"}
