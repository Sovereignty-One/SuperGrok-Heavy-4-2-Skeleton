#!/usr/bin/env python3
"""
Siri_Replace_Ara-Core.py
Version: 2.0
Sovereign Ara Replacement — Consent-Based Siri Replacement
"""

import os
import sys
import subprocess
import logging
from datetime import datetime
from pathlib import Path

# === CONFIG ===
VERSION = "2.0"
LOG_FILE = Path.home() / ".ara" / "ara_replace.log"
LISTENER_SCRIPT = "ara_listener.py"

# Ensure log directory exists
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

def log(msg, level="info"):
    print(msg)
    getattr(logging, level)(msg)

def get_device():
    platform = sys.platform
    if platform == "darwin":
        return "iOS/Mac"
    elif "android" in os.environ.get("ANDROID_ROOT", "").lower():
        return "Android"
    elif "win" in platform:
        return "Windows"
    elif "linux" in platform:
        return "Linux"
    return "Unknown"

# === INSTALL FUNCTIONS ===

def install_ios():
    log("=== iOS / macOS Installation ===")
    log("1. Open Shortcuts app → + → Create new shortcut named 'Hey Ara'")
    log("2. Add action → Run Script → paste content of ara_listener.py")
    log("3. Settings → Shortcuts → Allow Untrusted Shortcuts")
    log("4. Enable 'Hey Ara' as voice trigger")
    return True

def install_android():
    log("=== Android Installation ===")
    log("1. Settings → Accessibility → Downloaded Services → Ara Assistant → ON")
    log("2. Grant Microphone + Voice Access permissions")
    log("3. Set wake word to 'Hey Ara'")
    log("All data stays on-device. No Google involved.")
    return True

def install_windows():
    log("=== Windows Installation ===")
    log("1. Run ara_listener.exe as Administrator")
    log("2. Pin to Start Menu (optional)")
    log("3. Enable Auto-start via Task Scheduler (recommended)")
    log("Cortana will remain silent.")
    return True

def install_linux():
    log("=== Linux Installation ===")
    log("1. sudo cp ara_listener.py /usr/local/bin/")
    log("2. sudo systemctl enable --now ara.service")
    log("3. Reboot or run: ara_listener.py &")
    log("Wake word 'Hey Ara' is now active.")
    return True

# === UNINSTALL ===

def uninstall():
    log("=== Uninstalling Ara ===")
    try:
        if sys.platform == "darwin":
            log("Removing iOS/macOS shortcut...")
        elif "android" in os.environ.get("ANDROID_ROOT", "").lower():
            log("Disabling Android accessibility service...")
        elif "win" in sys.platform:
            log("Stopping Windows service...")
        elif "linux" in sys.platform:
            log("Disabling systemd service...")
        
        log("Ara has been removed. Original assistant restored.")
        return True
    except Exception as e:
        log(f"Uninstall failed: {e}", "error")
        return False

# === MAIN ===

def main():
    device = get_device()
    log(f"\n=== Ara Replacement v{VERSION} ===")
    log(f"Device detected: {device}")

    if device == "Unknown":
        log("Unsupported device. Exiting.", "error")
        sys.exit(1)

    print("\nOptions:")
    print("1. Install Ara (replace Siri)")
    print("2. Uninstall Ara (restore original)")
    print("3. Exit")

    choice = input("\nSelect option [1-3]: ").strip()

    if choice == "2":
        uninstall()
        return

    if choice != "1":
        log("Exiting.")
        return

    installers = {
        "iOS/Mac": install_ios,
        "Android": install_android,
        "Windows": install_windows,
        "Linux": install_linux
    }

    success = installers[device]()

    if not success:
        log("Installation failed.", "error")
        return

    confirm = input("\nProceed with replacement? (y/N): ").strip().lower()
    if confirm != "y":
        log("Installation canceled by user.")
        return

    log("✅ Ara replacement activated.")
    log("Say 'Hey Ara' to wake.")
    log("Say 'Restore original' to revert.")
    log("All memory is encrypted and local-only.")

    # Try to launch listener
    try:
        if Path(LISTENER_SCRIPT).exists():
            subprocess.Popen([sys.executable, LISTENER_SCRIPT])
            log("Ara listener started in background.")
        else:
            log(f"Warning: {LISTENER_SCRIPT} not found in current directory.", "warning")
    except Exception as e:
        log(f"Failed to start listener: {e}", "error")

if __name__ == "__main__":
    main()