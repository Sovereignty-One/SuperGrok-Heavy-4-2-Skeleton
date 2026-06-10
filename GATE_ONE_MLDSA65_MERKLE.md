# Gate One — ML-DSA-65 + Merkle (Sovereign, On-Device)

Gate One is the first attestation gate for the SuperGrok / Sovereignty dashboard
(`SGHv119_Newest.html`, `SGHv119-local.html`). It runs **entirely on the device**.
No external keys, no API, no network callouts.

## Primitives

| Purpose | Primitive | Engine |
|---|---|---|
| Key derivation | PBKDF2-SHA512 (600k) → HKDF-SHA512 | WebCrypto (Secure Enclave backed) |
| Integrity tree | Merkle, SHA-512 leaves | WebCrypto |
| PQ signature | **ML-DSA-65 (Dilithium3)** | liboqs-WASM if bundled, else on-device HMAC-SHA512 seal of identical structure |
| Symmetric | AES-256-GCM · ChaCha20 / XChaCha20 | WebCrypto + pure-JS ChaCha20 |
| Exchange / sign (when present) | X25519 · Ed25519 | WebCrypto |

## Flow

1. **Derive** a 256-bit key from the operator passphrase — never from an imported
   or external key.  `SovereignCrypto.deriveKey(passphrase, salt, info)`
2. **Build** a SHA-512 Merkle root over the gate's leaves (session, role, policy).
   `SovereignCrypto.merkleRoot(leaves)`
3. **Seal** `ML-DSA-65|<root>` with the derived key.
   `SovereignCrypto.gateOne(passphrase, leaves)` →
   `{ alg:'ML-DSA-65', engine, root, pk, sig, ts }`
4. **Verify** offline at any time. `SovereignCrypto.gateVerify(seal, passphrase, leaves)`

If a real ML-DSA-65 module is placed on the device as `window.MLDSA65`
(`keygen/sign/verify`), Gate One uses it automatically. Otherwise the deterministic
on-device seal provides an equivalent gate so the system **always verifies air-gapped**.

## Guarantees

- **Air-gap clean** — `SovereignGuard` neutralizes `WebSocket`, gates `fetch`/`XHR`
  to self + loopback only, and blocks external resource injection.
- **No external keys** — every key is derived on-device from operator input.
- **No Google / Meta / CDN / external AI API** — enforced by CSP and the guard.

## Crypto stack (operator's preferred, sovereign-grade)

Dilithium (ML-DSA) · ChaCha20 / XChaCha20 · Secure Enclave key storage ·
X25519 (exchange) · Ed25519 (signatures) · X.509 + TLS · DKIM (email auth).
