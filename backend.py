#!/usr/bin/env python3
"""
backend.py — Python Internal Backend (Port 9897)

Lightweight Flask service that handles:
  • /login          — issue HS256 JWT tokens
  • /secure-data    — validate JWT and return protected payload
  • /health         — shallow liveness probe

JWT signing key is retrieved from the secure enclave (env var → key file →
auto-generated), keeping it out of source code.

Run:
    pip install flask PyJWT
    python3 backend.py

Environment variables:
    SG_PORT          — listen port (default: 9897)
    JWT_SIGNING_KEY  — override the JWT signing key (optional)
"""

import time

from flask import Flask, jsonify, request

from secure_enclave import get_secure_key

try:
    import jwt
except ImportError as exc:
    raise SystemExit(
        "PyJWT is required: pip install PyJWT"
    ) from exc

import os

app = Flask(__name__)

JWT_SIGNING_KEY: str = get_secure_key("JWT_SIGNING_KEY")
_TOKEN_TTL = 7200  # seconds — 2 hours


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/login", methods=["POST"])
def login():
    """Issue a JWT for a username/role pair provided in the JSON body."""
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    role = str(data.get("role", "user")).strip()

    if not username:
        return jsonify({"error": "username is required"}), 400

    token = jwt.encode(
        {
            "username": username,
            "role": role,
            "exp": time.time() + _TOKEN_TTL,
        },
        JWT_SIGNING_KEY,
        algorithm="HS256",
    )
    return jsonify({"token": token})


@app.route("/secure-data")
def secure_data():
    """Return protected payload when a valid Bearer JWT is presented."""
    auth = request.headers.get("Authorization", "")
    token = auth.removeprefix("Bearer ").strip()
    if not token:
        return jsonify({"error": "Missing Authorization header"}), 401
    try:
        decoded = jwt.decode(token, JWT_SIGNING_KEY, algorithms=["HS256"])
        return jsonify({"message": "Secure access granted", "user": decoded})
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401


@app.route("/health")
def health():
    """Liveness probe used by Start_All.sh and Caddy."""
    return ("", 200)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("SG_PORT", 9897))
    app.run(host="127.0.0.1", port=port)
