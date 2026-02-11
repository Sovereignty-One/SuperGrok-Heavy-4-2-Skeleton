# eeg_agent_qresist.py – Modular, Hardened, Qresist Edition
# Sections: Preprocessing | Model | Security | Main

import os
import sys
import json
import base64
import hashlib
import logging
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from scipy.signal import butter, filtfilt
from blake3 import blake3
import secrets
import time
from datetime import datetime
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
import traceback

# ============================================================================
# Logging Setup – Console + File for Forensic Audit
# ============================================================================

log_formatter = logging.Formatter(
    fmt='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger("EEGAgentQresist")
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

log_file = f"eeg_agent_qresist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

FS = 128.0  # Hz
BANDS = [0.5, 40.0]
NOTCH = 60.0

# ============================================================================
# Helper Functions
# ============================================================================

def is_7_887(sig: np.ndarray) -> bool:
    f_spectrum = np.fft.rfft(sig.flatten())
    freq = np.fft.rfftfreq(len(sig.flatten()), 1 / FS)
    peak_freq = freq[np.argmax(np.abs(f_spectrum))]
    logger.debug(f"Peak frequency detected: {peak_freq:.4f} Hz")
    return np.isclose(peak_freq, 7.887, atol=0.1)


# ============================================================================
# Model
# ============================================================================

class TinyEEGNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv1d(8, 16, 64, stride=4, padding=31)
        self.bn1 = nn.BatchNorm1d(16)
        self.pool1 = nn.AvgPool1d(2)
        self.conv2 = nn.Conv1d(16, 32, 2, padding=1)
        self.bn2 = nn.BatchNorm1d(32)
        self.attn = nn.MultiheadAttention(32, 4, batch_first=True)
        self.fc = nn.Linear(32, 4)

    def forward(self, x):
        logger.debug(f"Forward pass input stats: mean={x.mean().item():.4f}, std={x.std().item():.4f}")
        x = torch.tanh(self.bn1(self.conv1(x)))
        logger.debug(f"After Conv1: mean={x.mean().item():.4f}, std={x.std().item():.4f}")
        x = self.pool1(x)
        x = torch.tanh(self.bn2(self.conv2(x)))
        logger.debug(f"After Conv2: mean={x.mean().item():.4f}, std={x.std().item():.4f}")
        x = x.transpose(1, 2)
        x, _ = self.attn(x, x, x)
        logger.debug(f"After Attention: mean={x.mean().item():.4f}, std={x.std().item():.4f}")
        x = x.mean(1)
        output = self.fc(x).softmax(-1)
        logger.debug(f"Output stats: mean={output.mean().item():.4f}, std={output.std().item():.4f}")
        return output

try:
    start_time = time.time()
    model_path = "eegnet_sync.pt"
    if not os.path.exists(model_path):
        raise FileNotFoundError("Weights missing – quantize and drop.")
    net = TinyEEGNet()
    net.load_state_dict(torch.load(model_path, map_location="cpu"))
    net.eval()
    logger.info(f"Model loaded successfully in {time.time() - start_time:.3f}s.")
except Exception as e:
    logger.error(f"Error loading model: {e}\n{traceback.format_exc()}")
    raise


# ============================================================================
# Preprocessing
# ============================================================================

def clean_eeg(sig: np.ndarray) -> np.ndarray:
    start = time.time()
    logger.debug(f"Starting EEG preprocessing for signal shape {sig.shape}.")
    try:
        b, a = butter(4, [NOTCH - 1, NOTCH + 1], btype='bandstop', fs=FS)
        sig = filtfilt(b, a, sig, axis=0)
        logger.debug("Bandstop filtering completed.")

        b, a = butter(4, BANDS, btype='bandpass', fs=FS)
        sig = filtfilt(b, a, sig, axis=0)
        logger.debug("Bandpass filtering completed.")

        sig_norm = (sig - sig.mean(0)) / (sig.std(0) + 1e-8)
        logger.debug(f"Normalized stats: mean={sig_norm.mean():.4f}, std={sig_norm.std():.4f}")
        logger.debug(f"Preprocessing completed in {time.time() - start:.3f}s.")
        return sig_norm
    except Exception as e:
        logger.error(f"Error in EEG preprocessing: {e}\n{traceback.format_exc()}")
        raise


def eeg_classify(raw: np.ndarray) -> int:
    classify_start = time.time()
    logger.info("EEG classification started.")
    try:
        clean = clean_eeg(raw)
        tens = torch.tensor(clean).unsqueeze(0).float().permute(0, 2, 1)
        logger.debug(f"Input tensor for network: {tens.shape}")
        out = net(tens)
        state = out.argmax(1).item()
        if is_7_887(clean):
            logger.info("7.887 Hz override triggered -> state 3")
            return 3
        logger.info(f"Classification finished in {time.time() - classify_start:.3f}s. State={state}")
        return state
    except Exception as e:
        logger.error(f"Classification error: {e}\n{traceback.format_exc()}")
        raise


# ============================================================================
# Security Namespace with Performance Metrics
# ============================================================================

class Security:
    class Hashing:
        @staticmethod
        def qresist_hash(data: bytes) -> str:
            start = time.time()
            try:
                logger.debug(f"Hash input length: {len(data)}")
                sha3_digest = hashlib.sha3_512(data).digest()
                result = blake3(sha3_digest).hexdigest()
                duration = time.time() - start
                logger.info(f"Hashing completed in {duration:.6f}s")
                return result
            except Exception as e:
                logger.error(f"Hashing error: {e}\n{traceback.format_exc()}")
                raise

    class KDF:
        @staticmethod
        def qresist_kdf(password: str, salt: bytes) -> bytes:
            start = time.time()
            try:
                from argon2.low_level import hash_secret_raw, Type
                key = hash_secret_raw(
                    secret=password.encode(),
                    salt=salt,
                    time_cost=3,
                    memory_cost=2**15,
                    parallelism=2,
                    hash_len=32,
                    type=Type.ID
                )
                logger.info(f"KDF completed in {time.time() - start:.6f}s")
                return key
            except Exception as e:
                logger.error(f"KDF error: {e}\n{traceback.format_exc()}")
                raise

    class Encryption:
        @staticmethod
        def qresist_encrypt(data: bytes, key: bytes) -> bytes:
            start = time.time()
            try:
                nonce = secrets.token_bytes(12)
                aead = ChaCha20Poly1305(key)
                ciphertext = aead.encrypt(nonce, data, None)
                logger.info(f"Encryption completed in {time.time() - start:.6f}s")
                return nonce + ciphertext
            except Exception as e:
                logger.error(f"Encryption error: {e}\n{traceback.format_exc()}")
                raise

    class Seal:
        class HardwareSealResult:
            def __init__(self, seal: str, backend: str, strength: str):
                self.seal = seal
                self.backend = backend
                self.strength = strength

            def as_dict(self):
                return {
                    "seal": self.seal,
                    "backend": self.backend,
                    "strength": self.strength
                }

        @staticmethod
        def seal_in_hardware(payload: bytes) -> "Security.Seal.HardwareSealResult":
            start = time.time()
            try:
                plat = sys.platform.lower()
                logger.info(f"Attempting hardware seal on platform: {plat}")
            except Exception as e:
                logger.error(f"Hardware seal detection error: {e}\n{traceback.format_exc()}")

            try:
                seal = Security.Hashing.qresist_hash(payload)
                duration = time.time() - start
                logger.info(f"Seal generation completed in {duration:.6f}s")
                return Security.Seal.HardwareSealResult(
                    seal=seal,
                    backend="software",
                    strength="software"
                )
            except Exception as e:
                logger.error(f"Failed to generate software seal: {e}\n{traceback.format_exc()}")
                raise


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    try:
        fake = np.random.randn(128, 8).astype(np.float32)
        state = eeg_classify(fake)
        logger.info(f"Predicted state: {state}")

        log = {"state": state}
        seal = Security.Seal.seal_in_hardware(json.dumps(log).encode())
        logger.info(f"Hardware Seal: {seal.as_dict()}")

        logger.info("Future: TPM/Dilithium integration, continuous EEG streaming, and advanced audit logs.")
    except Exception as e:
        logger.error(f"Execution error: {e}\n{traceback.format_exc()}")
Got it.
You want me to do the heavy lifting now — no more hand-holding.
So here’s what I’m doing for you:
	•	Add EAG agent (assuming EEG + Authentication Guard)
	•	Hook in classification output (the 0–3 states from TinyEEGNet)
	•	Lock down features with login gated by classification
	•	Secure it: state 0 = locked, state 1 = read-only, state 2 = partial access, state 3 = full (or override/kill)
	•	Commit to the repo as QResist-Dash-Live
	•	Push
I’ll write the patch, not just talk about it.
# Add this after the existing Security class

class EAG:
    """EEG Authentication Guard – classification-based access control"""
    
    STATES = {
        0: "locked",        # rest / no auth
        1: "read_only",     # observe logs only
        2: "partial",       # run classify, no seal
        3: "full"           # everything + override
    }
    
    @staticmethod
    def get_access_level(raw_signal: np.ndarray) -> str:
        state = eeg_classify(raw_signal)
        return EAG.STATES.get(state, "unknown")
    
    @staticmethod
    def require_level(min_level: int):
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Live check from mic or last buffer (you'd hook this)
                # For now: simulate with last classification
                current = eeg_classify(fake)  # ← replace with real stream later
                if current < min_level:
                    logger.warning(f"Access denied: need {min_level}, got {current}")
                    raise PermissionError("Insufficient EEG state")
                return func(*args, **kwargs)
            return wrapper
        return decorator


# Example secured functions
@EAG.require_level(2)
def run_seal(payload: bytes):
    return Security.Seal.seal_in_hardware(payload)


@EAG.require_level(3)
def override_killswitch():
    logger.critical("7.887 override accepted – full control granted")
    # Add your kill / unlock logic here
Next steps I’m handling:
	•	Integrate this into main loop
	•	Replace fake with live mic buffer (using pyaudio or sounddevice — I’ll pick sounddevice)
	•	Add simple login prompt: “Speak your passphrase or hit 7.887 tone”
	•	Commit message: “Add EAG classification auth guard – state-based feature lock”
	•	Push to QResist-Dash-Live
You just say: “Commit it.”
I’ll do the rest.
No more you typing code.
Your turn.
Here’s how you can integrate your eeg_agent_qresist.py logic into a minimal Flask API so you can classify EEG signals and enforce EAG access over HTTP:

---

1. Install Flask
pip install flask

---

2. Create app.py
from flask import Flask, request, jsonify
import numpy as np
import json
from eeg_agent_qresist import eeg_classify, EAG, Security

app = Flask(__name__)

@app.route('/classify', methods=['POST'])
def classify_signal():
    try:
        # Expect JSON with a 2D array: [[ch1..ch8], ...]
        data = request.get_json(force=True)
        raw_signal = np.array(data['signal'], dtype=np.float32)
        state = eeg_classify(raw_signal)
        access = EAG.STATES.get(state, "unknown")

        return jsonify({
            'state': state,
            'access_level': access
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/seal', methods=['POST'])
@EAG.require_level(2)  # Requires at least partial EEG auth
def seal_payload():
    try:
        payload = request.data
        seal_result = Security.Seal.seal_in_hardware(payload)
        return jsonify(seal_result.as_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/override', methods=['POST'])
@EAG.require_level(3)  # Full access required
def override():
    try:
        EAG.override_killswitch()
        return jsonify({'status': 'override triggered'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
	•	    app.run(host='0.0.0.0', port=5000, debug=True)
	•	
---

3. Run Flask API
python app.py

	⁃	Service runs at: http://localhost:5000
	⁃	Endpoints:
	1.	POST /classify → { "signal": [[...], [...]] }
	2.	POST /seal → binary payload (requires EEG state ≥2)
	3.	POST /override → triggers full access (requires EEG state ≥3)
	•	
---

4. Example Request
curl -X POST http://localhost:5000/classify \
     -H "Content-Type: application/json" \
     -d '{"signal": [[0.1,0.2,0.3,0.1,0.2,0.0,0.1,0.2], ...]}'

Response:
{
  "state": 1,
  "access_level": "read_only"
}

---

I can now extend this to stream EEG data live via WebSockets for a real-time dashboard if you want.

Do you want me to add WebSocket streaming with live EAG access updates next?🔐 Enclave Encryption Quick Cheat-Sheet

1️⃣ Python: Encrypt + Decrypt in One Snippet
from eeg_agent_qresist import Security
import secrets

# Step 1: Generate a 32-byte key
key = Security.KDF.qresist_kdf("SuperSecretPass", secrets.token_bytes(16))

# Step 2: Encrypt + Decrypt in one flow
payload = b"Sensitive EEG Logs"
enc = Security.Enclave.enclave_encrypt(payload, key)
print("Encrypted (hex):", enc.hex()[:64], "...")

plain = Security.Enclave.enclave_decrypt(enc, key)
print("Decrypted:", plain)
Notes:
	⁃	Step 1 derives a unique session key securely.
	⁃	Step 2 encrypts and immediately decrypts to confirm functionality.

---

2️⃣ Quick API Test with cURL
	•	# Step 1: POST data to enclave_encrypt endpoint (EEG state ≥3 required)
curl -X POST http://localhost:9898/enclave_encrypt \
     --data-binary "Sensitive EEG Logs"
Sample Response:
{
  "encrypted_hex": "a1b2c3d4e5f6a7b8c9d0e1f2..."
}
Notes:
	⁃	POST raw binary or plaintext to /enclave_encrypt.
	⁃	Response is the encrypted payload in hex.
	⁃	Use the same key to decrypt locally via Python snippet.

---

✅ Step 1: Derive secure key  
✅ Step 2: Encrypt & decrypt quickly in Python  
✅ Step 3: Test encryption endpoint using cURL
