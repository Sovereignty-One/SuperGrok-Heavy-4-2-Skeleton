#!/usr/bin/env python3
"""
Security Sentinel — Active Safety Agent
=========================================
A persistent watchdog agent that runs continuously to enforce safety
protocols and protect against attacks.

Capabilities:
  - Periodic file-integrity checks (SHA-256 baseline)
  - Rate-limit monitoring on the access audit log
  - Connection-burst / brute-force detection
  - Tamper detection on critical configuration files
  - Structured JSON event logging

Usage:
  python security_sentinel.py            # foreground
  python security_sentinel.py --daemon   # background (writes PID file)
  python security_sentinel.py --check    # single pass then exit

Environment variables (all optional):
  SENTINEL_INTERVAL   seconds between sweeps  (default 30)
  SENTINEL_LOG_DIR    log directory            (default ./logs)
  SENTINEL_PID_FILE   PID file path            (default ./sentinel.pid)
  RATE_LIMIT_WINDOW   seconds for rate window  (default 60)
  RATE_LIMIT_MAX      max events in window     (default 100)
"""

import hashlib
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SWEEP_INTERVAL = int(os.getenv("SENTINEL_INTERVAL", "30"))
LOG_DIR = os.getenv("SENTINEL_LOG_DIR", "./logs")
PID_FILE = os.getenv("SENTINEL_PID_FILE", "./sentinel.pid")
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "100"))

# Files whose integrity is tracked between sweeps
WATCHED_FILES = [
    "Unified_Server.js",
    "package.json",
    ".env.example",
    "Start_All.sh",
]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
os.makedirs(LOG_DIR, exist_ok=True)

SENTINEL_LOG = os.path.join(LOG_DIR, "sentinel.jsonl")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SENTINEL] %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(LOG_DIR, "sentinel.log"), mode="a"),
    ],
)
logger = logging.getLogger("sentinel")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _emit(event: str, detail: str, level: str = "INFO"):
    """Append a structured JSON event to the sentinel log."""
    entry = {
        "ts": _utcnow(),
        "event": event,
        "detail": detail[:500],
        "level": level,
    }
    with open(SENTINEL_LOG, "a") as fh:
        fh.write(json.dumps(entry) + "\n")
    getattr(logger, level.lower(), logger.info)(
        "%s — %s", event, detail[:200]
    )


def _sha256(filepath: str) -> str | None:
    """Return hex SHA-256 of *filepath*, or None if unreadable."""
    try:
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None

# ---------------------------------------------------------------------------
# Integrity checker
# ---------------------------------------------------------------------------

class IntegrityChecker:
    """Tracks SHA-256 hashes and raises alerts on unexpected changes."""

    def __init__(self, watched: list[str]):
        self._baseline: dict[str, str | None] = {}
        self._watched = watched
        self._build_baseline()

    def _build_baseline(self):
        for fp in self._watched:
            self._baseline[fp] = _sha256(fp)
        _emit("baseline_set", f"Tracking {len(self._baseline)} files")

    def sweep(self) -> list[str]:
        """Return list of files whose hash changed since last sweep."""
        alerts: list[str] = []
        for fp in self._watched:
            current = _sha256(fp)
            previous = self._baseline.get(fp)
            if previous is not None and current != previous:
                msg = f"File changed: {fp}"
                alerts.append(msg)
                _emit("integrity_alert", msg, "WARNING")
            self._baseline[fp] = current
        return alerts

# ---------------------------------------------------------------------------
# Rate-limit monitor
# ---------------------------------------------------------------------------

class RateLimitMonitor:
    """Watches the access audit log for connection-burst patterns."""

    def __init__(self, log_path: str, window: int, threshold: int):
        self._log_path = log_path
        self._window = window
        self._threshold = threshold

    def check(self) -> list[str]:
        alerts: list[str] = []
        try:
            if not os.path.exists(self._log_path):
                return alerts
            cutoff = time.time() - self._window
            recent = 0
            with open(self._log_path, "r") as fh:
                for line in fh:
                    try:
                        entry = json.loads(line)
                        ts = entry.get("ts", "")
                        entry_time = datetime.fromisoformat(ts).timestamp()
                        if entry_time >= cutoff:
                            recent += 1
                    except (json.JSONDecodeError, ValueError, TypeError):
                        continue
            if recent > self._threshold:
                msg = (
                    f"Rate limit exceeded: {recent} events in "
                    f"{self._window}s (threshold {self._threshold})"
                )
                alerts.append(msg)
                _emit("rate_limit_alert", msg, "WARNING")
        except OSError as exc:
            _emit("rate_monitor_error", str(exc), "ERROR")
        return alerts

# ---------------------------------------------------------------------------
# Sentinel agent
# ---------------------------------------------------------------------------

class SecuritySentinel:
    """Persistent safety agent — runs sweep loops until stopped."""

    def __init__(self):
        self._running = False
        self._integrity = IntegrityChecker(WATCHED_FILES)
        access_log = os.path.join(LOG_DIR, "access.jsonl")
        self._rate_monitor = RateLimitMonitor(
            access_log, RATE_LIMIT_WINDOW, RATE_LIMIT_MAX
        )

    # -- lifecycle -----------------------------------------------------------

    def start(self, *, single_pass: bool = False):
        self._running = True
        _emit("sentinel_start", f"interval={SWEEP_INTERVAL}s")
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        if single_pass:
            self._sweep()
            return

        while self._running:
            self._sweep()
            for _ in range(SWEEP_INTERVAL):
                if not self._running:
                    break
                time.sleep(1)

        _emit("sentinel_stop", "Clean shutdown")

    def stop(self):
        self._running = False

    def _handle_signal(self, signum, _frame):
        _emit("signal_received", f"sig={signum}")
        self.stop()

    # -- sweep ---------------------------------------------------------------

    def _sweep(self):
        _emit("sweep_start", _utcnow())

        integrity_alerts = self._integrity.sweep()
        rate_alerts = self._rate_monitor.check()

        total = len(integrity_alerts) + len(rate_alerts)
        status = "clean" if total == 0 else f"{total} alert(s)"
        _emit("sweep_complete", status)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    daemon_mode = "--daemon" in sys.argv
    check_mode = "--check" in sys.argv

    if daemon_mode:
        pid = os.getpid()
        Path(PID_FILE).write_text(str(pid))
        _emit("daemon_pid", str(pid))

    sentinel = SecuritySentinel()

    try:
        sentinel.start(single_pass=check_mode)
    finally:
        if daemon_mode and os.path.exists(PID_FILE):
            os.remove(PID_FILE)


if __name__ == "__main__":
    main()
