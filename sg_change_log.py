#!/usr/bin/env python3
"""
sg_change_log.py

Append-only change log for a multi-agent repo:
- Records what changed (git diff), where (files), why, when, and which model/tool/actor.
- Hash-chains entries for tamper-evidence.
- Optionally saves sanitized patch files.
- Can verify the log chain integrity.

Requires: git installed and repo initialized.
No external Python deps.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "sg_change_log.jsonl"
PATCH_DIR = LOG_DIR / "patches"

DEFAULT_SECRET_PATTERNS = [
    # Common API key env names and token-ish strings
    r"(OPENAI|ANTHROPIC|XAI|GROK|KEYCLOAK|OIDC|JWT|BEARER|TOKEN|API_KEY)\s*=\s*['\"][^'\"]+['\"]",
    r"Authorization:\s*Bearer\s+[A-Za-z0-9\-\._~\+\/]+=*",
    r"sk-[A-Za-z0-9]{10,}",            # OpenAI-style
    r"sk-ant-[A-Za-z0-9\-_]{10,}",     # Anthropic-style
]


@dataclass(frozen=True)
class ChangeEntry:
    id: str
    timestamp_utc: str
    actor: str
    tool: str
    model: str
    why: str
    repo_head: str
    branch: str
    files_changed: List[str]
    diff_stat: str
    diff_sha256: str
    prev_entry_hash: str
    entry_hash: str


def run(cmd: List[str], cwd: Path) -> Tuple[int, str]:
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    out = (p.stdout or "") + (p.stderr or "")
    return p.returncode, out.rstrip()


def is_git_repo(root: Path) -> bool:
    return run(["git", "rev-parse", "--is-inside-work-tree"], root)[0] == 0


def git_branch_head(root: Path) -> Tuple[str, str]:
    _, branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], root)
    _, head = run(["git", "rev-parse", "HEAD"], root)
    return branch.strip(), head.strip()


def git_diff_name_only(root: Path, staged: bool) -> List[str]:
    cmd = ["git", "diff", "--name-only"]
    if staged:
        cmd.append("--cached")
    _, out = run(cmd, root)
    return [line.strip() for line in out.splitlines() if line.strip()]


def git_diff_stat(root: Path, staged: bool) -> str:
    cmd = ["git", "diff", "--stat"]
    if staged:
        cmd.append("--cached")
    _, out = run(cmd, root)
    return out.strip()


def git_diff_patch(root: Path, staged: bool) -> str:
    cmd = ["git", "diff"]
    if staged:
        cmd.append("--cached")
    _, out = run(cmd, root)
    return out


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", errors="replace")).hexdigest()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def next_entry_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def load_last_entry_hash() -> str:
    if not LOG_FILE.exists():
        return "GENESIS"
    last_line = None
    with LOG_FILE.open("rb") as f:
        for line in f:
            if line.strip():
                last_line = line
    if not last_line:
        return "GENESIS"
    obj = json.loads(last_line.decode("utf-8"))
    return obj.get("entry_hash", "GENESIS")


def sanitize_text(text: str, patterns: List[str]) -> str:
    redacted = text
    for pat in patterns:
        redacted = re.sub(pat, "[REDACTED]", redacted, flags=re.IGNORECASE)
    return redacted


def compute_entry_hash(payload: Dict[str, Any]) -> str:
    # Stable JSON
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256_text(blob)


def append_entry(entry: ChangeEntry) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")


def write_patch(entry_id: str, patch: str) -> Path:
    PATCH_DIR.mkdir(parents=True, exist_ok=True)
    p = PATCH_DIR / f"{entry_id}.patch"
    p.write_text(patch, encoding="utf-8")
    return p


def verify_log() -> int:
    if not LOG_FILE.exists():
        print("No log file found.")
        return 1

    prev = "GENESIS"
    ok = True

    with LOG_FILE.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            if not line.strip():
                continue
            obj = json.loads(line)
            prev_in = obj.get("prev_entry_hash", "")
            if prev_in != prev:
                print(f"[FAIL] Line {i}: prev hash mismatch (expected {prev}, got {prev_in})")
                ok = False

            # Recompute hash excluding entry_hash itself
            payload = dict(obj)
            entry_hash = payload.pop("entry_hash", "")
            recomputed = compute_entry_hash(payload)
            if entry_hash != recomputed:
                print(f"[FAIL] Line {i}: entry hash mismatch")
                ok = False

            prev = entry_hash

    if ok:
        print("[OK] Log chain verified.")
        return 0
    return 2


def main() -> int:
    ap = argparse.ArgumentParser(description="Append-only multi-agent change logger (hash-chained).")
    ap.add_argument("--actor", default=os.environ.get("SG_ACTOR", "unknown"), help="Who/what made the change")
    ap.add_argument("--tool", default=os.environ.get("SG_TOOL", "unknown"), help="gpt|grok|claude|copilot|agent")
    ap.add_argument("--model", default=os.environ.get("SG_MODEL", "unknown"), help="Model identifier")
    ap.add_argument("--why", default=os.environ.get("SG_WHY", "no reason provided"), help="Why this change happened")
    ap.add_argument("--staged", action="store_true", help="Log staged changes (git diff --cached)")
    ap.add_argument("--write-patch", action="store_true", help="Save sanitized patch into logs/patches/<id>.patch")
    ap.add_argument("--verify", action="store_true", help="Verify the log chain integrity")
    ap.add_argument("--no-sanitize", action="store_true", help="Do not redact secrets from patch (not recommended)")
    args = ap.parse_args()

    if args.verify:
        return verify_log()

    root = Path.cwd()
    if not is_git_repo(root):
        print("Not a git repo. Initialize git or run from repo root.")
        return 1

    branch, head = git_branch_head(root)
    files = git_diff_name_only(root, staged=args.staged)
    stat = git_diff_stat(root, staged=args.staged)
    patch = git_diff_patch(root, staged=args.staged)

    if not files and not patch.strip():
        print("No changes detected (git diff is empty). Nothing to log.")
        return 0

    patterns = [] if args.no_sanitize else DEFAULT_SECRET_PATTERNS
    patch_sanitized = sanitize_text(patch, patterns)
    diff_hash = sha256_text(patch_sanitized)

    entry_id = next_entry_id()
    prev_hash = load_last_entry_hash()

    payload = {
        "id": entry_id,
        "timestamp_utc": utc_now_iso(),
        "actor": args.actor,
        "tool": args.tool,
        "model": args.model,
        "why": args.why,
        "repo_head": head,
        "branch": branch,
        "files_changed": files,
        "diff_stat": stat,
        "diff_sha256": diff_hash,
        "prev_entry_hash": prev_hash,
    }
    entry_hash = compute_entry_hash(payload)

    entry = ChangeEntry(entry_hash=entry_hash, **payload)  # type: ignore[arg-type]
    append_entry(entry)

    if args.write_patch:
        p = write_patch(entry_id, patch_sanitized)
        print(f"[OK] wrote patch: {p}")

    print(f"[OK] logged entry: {LOG_FILE} id={entry_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
