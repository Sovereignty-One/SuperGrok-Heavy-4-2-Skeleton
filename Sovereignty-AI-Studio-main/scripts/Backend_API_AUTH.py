from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from pqcrypto.sign.dilithium2 import verify
from totp import TOTP  # your totp.js wrapper
import json, time

router = APIRouter(prefix="/auth")

class LoginRequest(BaseModel):
    pubkey: str  # hex
    signature: str  # hex of payload
    totp_code: str

@router.post("/login")
async def login(req: LoginRequest):
    # Payload = timestamp + role
    payload = f"{int(time.time())}:admin"  # or user/dev
    try:
        if not verify(bytes.fromhex(req.pubkey), payload.encode(), bytes.fromhex(req.signature)):
            raise HTTPException(403, "Invalid signature")
    except:
        raise HTTPException(403, "Signature fail")

    # TOTP check
    if not TOTP.verify(req.totp_code, secret="your-base32-secret"):
        raise HTTPException(401, "Bad TOTP")

    # Token: just json signed
    token = {"user": "internal", "role": "admin", "iat": time.time()}
    signed_token = sign(bytes.fromhex(req.pubkey), json.dumps(token).encode()).hex()  # reuse key

    log_entry = {"event": "login", "role": "admin", "ts": time.time()}
    # append to /logs/auth.jsonl

    return {"token": signed_token}
