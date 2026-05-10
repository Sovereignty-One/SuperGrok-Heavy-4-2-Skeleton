# tests/test_quadratchet_benchmark.py
"""Benchmark and JSON persistence tests for QuadRatchetSession."""

import json
import time
import pathlib
import pytest
from session import QuadRatchetSession

BENCHMARK_FILE = pathlib.Path("benchmark_results.log")


def serialize_session_to_json(session: QuadRatchetSession) -> str:
    """Serialize a session to a JSON string, including Merkle leaves."""
    return json.dumps({
        "cookie": session.cookie.hex(),
        "send_counter": session._send_counter,
        "recv_counter": session._recv_counter,
        "root_key_snapshot": session._root_key_snapshot.hex(),
        "pq_seed_snapshot": session._pq_seed_snapshot.hex(),
        "double": {
            "send_chain": session.double.send_chain.hex(),
            "recv_chain": session.double.recv_chain.hex(),
            "root_key": session.double.root_key.hex(),
            "dh_pub": session.double.dh_public_bytes.hex(),
        },
        "quad": {
            "signing_key": session.quad.signing_key.hex(),
            "merkle_leaves": [leaf.hex() for leaf in session.quad.tree.leaves],
        },
    })


def deserialize_session_from_json(json_str: str) -> QuadRatchetSession:
    """Create a QuadRatchetSession from JSON state."""
    data = json.loads(json_str)
    session = QuadRatchetSession()
    session.cookie = bytes.fromhex(data["cookie"])
    session._send_counter = data["send_counter"]
    session._recv_counter = data["recv_counter"]
    session._root_key_snapshot = bytes.fromhex(data["root_key_snapshot"])
    session._pq_seed_snapshot = bytes.fromhex(data["pq_seed_snapshot"])

    # Restore DoubleRatchetState
    session.double.send_chain = bytes.fromhex(data["double"]["send_chain"])
    session.double.recv_chain = bytes.fromhex(data["double"]["recv_chain"])
    session.double.root_key = bytes.fromhex(data["double"]["root_key"])
    # Keep session.double.dh_private as generated; we only need public bytes for proof

    # Restore Quad SLH state & Merkle tree
    session.quad.signing_key = bytes.fromhex(data["quad"]["signing_key"])
    session.quad.tree.leaves = [bytes.fromhex(x) for x in data["quad"]["merkle_leaves"]]
    session.quad.tree.recompute_root()

    return session


def test_benchmark_and_log(tmp_path):
    """Benchmark encryption of 1000 messages and log results to a file."""
    session = QuadRatchetSession()
    messages = [f"msg-{i}".encode() for i in range(1000)]
    start = time.time()

    for msg in messages:
        session.encrypt(msg)

    duration = time.time() - start
    rate = len(messages) / duration

    log_entry = f"Encrypted {len(messages)} messages in {duration:.2f}s ({rate:.2f} msg/s)\n"
    BENCHMARK_FILE.write_text(log_entry)

    assert BENCHMARK_FILE.exists()
    contents = BENCHMARK_FILE.read_text()
    assert "Encrypted 1000 messages" in contents


def test_full_json_serialization_and_reload():
    """Serialize full session to JSON, reload, and verify Merkle integrity."""
    session = QuadRatchetSession()
    blobs = []

    for i in range(5):
        blob, proof = session.encrypt(f"persist-{i}".encode())
        blobs.append((blob, proof))

    # Serialize to JSON
    json_state = serialize_session_to_json(session)

    # Deserialize session
    restored = deserialize_session_from_json(json_state)

    # Verify that the Merkle root matches after reload
    assert restored.quad.tree.root == session.quad.tree.root

    # Verify decryption works with restored session
    for i, (blob, proof) in enumerate(blobs):
        decrypted = restored.decrypt(blob)
        assert decrypted == f"persist-{i}".encode()
