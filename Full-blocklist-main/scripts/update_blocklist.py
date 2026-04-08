#!/usr/bin/env python3
"""
Fetches entries from upstream blocklist sources, merges them with the
existing custom entries in Full_Blocklist, deduplicates, and writes the
result back to the file.
"""

import re
import ssl
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BLOCKLIST_PATH = REPO_ROOT / "Full_Blocklist"

# Upstream hosts-format sources to pull from every run.
# Each URL must return a plain-text file with lines like:
#   0.0.0.0 example.com   or   127.0.0.1 example.com
UPSTREAM_SOURCES = [
    # StevenBlack unified hosts (ads + malware)
    "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts",
    # AdAway default blocklist
    "https://adaway.org/hosts.txt",
    # Peter Lowe's ad / tracking server list
    "https://pgl.yoyo.org/adservers/serverlist.php?hostformat=hosts&showintro=0&mimetype=plaintext",
]

# Regex that matches a valid hosts-file block entry
HOSTS_LINE_RE = re.compile(
    r"^\s*(0\.0\.0\.0|127\.0\.0\.1)\s+([\w\.\-]+)\s*(?:#.*)?$"
)


def fetch_entries(url: str) -> set[str]:
    """Download *url* and return a set of 'domain' strings."""
    entries: set[str] = set()
    try:
        ssl_ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers={"User-Agent": "blocklist-updater/1.0"})
        with urllib.request.urlopen(req, timeout=30, context=ssl_ctx) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8", errors="replace").strip()
                m = HOSTS_LINE_RE.match(line)
                if m:
                    entries.add(m.group(2).lower())
    except Exception as exc:  # noqa: BLE001
        print(f"[WARN] Could not fetch {url}: {exc}", file=sys.stderr)
    return entries


def load_custom_entries(path: Path) -> tuple[list[str], set[str]]:
    """
    Read the existing blocklist file and return:
      - header_lines : lines before any 0.0.0.0 block entry (preserved verbatim)
      - custom_domains: set of domains already in the file
    """
    header_lines: list[str] = []
    custom_domains: set[str] = set()
    found_first_entry = False

    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            stripped = line.rstrip("\n")
            m = HOSTS_LINE_RE.match(stripped)
            if m:
                found_first_entry = True
                custom_domains.add(m.group(2).lower())
            else:
                if not found_first_entry:
                    header_lines.append(stripped)

    return header_lines, custom_domains


def main() -> None:
    if not BLOCKLIST_PATH.exists():
        print(f"[ERROR] Blocklist not found at {BLOCKLIST_PATH}", file=sys.stderr)
        sys.exit(1)

    header_lines, existing_domains = load_custom_entries(BLOCKLIST_PATH)

    # Collect all upstream domains
    upstream_domains: set[str] = set()
    for url in UPSTREAM_SOURCES:
        print(f"[INFO] Fetching {url}")
        upstream_domains |= fetch_entries(url)

    print(f"[INFO] Upstream entries fetched: {len(upstream_domains)}")

    all_domains = existing_domains | upstream_domains
    print(f"[INFO] Total unique domains after merge: {len(all_domains)}")

    # Write back: header first, then sorted block entries
    with BLOCKLIST_PATH.open("w", encoding="utf-8") as fh:
        for line in header_lines:
            fh.write(line + "\n")
        # Ensure exactly one blank line between the header and the block entries
        trimmed = [l for l in header_lines if l.strip()]
        if trimmed:
            fh.write("\n")
        for domain in sorted(all_domains):
            fh.write(f"0.0.0.0 {domain}\n")

    print(f"[INFO] {BLOCKLIST_PATH} updated successfully.")


if __name__ == "__main__":
    main()
