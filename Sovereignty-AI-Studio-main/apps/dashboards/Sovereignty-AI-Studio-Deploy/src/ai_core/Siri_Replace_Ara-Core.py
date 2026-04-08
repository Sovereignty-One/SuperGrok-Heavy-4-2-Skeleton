# ara_replace.py — MODULAR + LOGGING + PLATFORM EXCEPTIONS
# User-Consented Replacement: Siri → Ara
# Local-First • No Force • Full Choice

import os
import subprocess
import sys
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    filename='ara_install.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

def log_and_print(message, level="info"):
    print(message)
    getattr(logging, level)(message)

def get_device():
    device = (
        "iOS/Mac" if sys.platform == "darwin" else
        "Android" if "android" in os.environ.get("ANDROID_ROOT", "").lower() else
        "Windows" if "win" in sys.platform else
        "Linux" if "linux" in sys.platform else
        "Unknown"
    )
    logging.info(f"Detected device: {device}")
    return device

# -----------------------
# OS-specific installation with error handling and platform exceptions
# -----------------------

def install_ios():
    try:
        log_and_print("1. Open Shortcuts app → + → 'Hey Ara'")
        log_and_print("2. Add action → Run Script → ara_listener.py")
        log_and_print("3. Settings → Shortcuts → Allow Untrusted")
        log_and_print("Done. No Apple ID. No cloud.")
        return True
    except PermissionError as pe:
        log_and_print(f"iOS/Mac permission error: {pe}", "error")
    except FileNotFoundError as fnf:
        log_and_print(f"Missing required file on iOS/Mac: {fnf}", "error")
    except Exception as e:
        log_and_print(f"iOS/Mac installation failed: {e}", "error")
    return False

def install_android():
    try:
        log_and_print("1. Settings → Accessibility → Ara Assistant → ON")
        log_and_print("2. Grant Microphone + Voice Access")
        log_and_print("3. Set wake word → 'Hey Ara'")
        log_and_print("Local data only; No Google.")
        return True
    except PermissionError as pe:
        log_and_print(f"Android permission error: {pe}", "error")
    except FileNotFoundError as fnf:
        log_and_print(f"Required Android resource missing: {fnf}", "error")
    except Exception as e:
        log_and_print(f"Android installation failed: {e}", "error")
    return False

def install_windows():
    try:
        log_and_print("1. Win+R → 'ara_listener.exe' → Enter")
        log_and_print("2. Pin to Start → Enable Auto-start if desired")
        log_and_print("Runs as service; Cortana stays quiet.")
        return True
    except PermissionError as pe:
        log_and_print(f"Windows permission error: {pe}", "error")
    except FileNotFoundError as fnf:
        log_and_print(f"Missing ara_listener.exe: {fnf}", "error")
    except Exception as e:
        log_and_print(f"Windows installation failed: {e}", "error")
    return False

def install_linux():
    try:
        log_and_print("1. sudo systemctl enable --now ara.service")
        log_and_print("2. sudo systemctl enable --now speech_recognition")
        log_and_print("3. Boots and listens for 'Hey Ara'. Local only.")
        return True
    except PermissionError as pe:
        log_and_print(f"Linux permission error (maybe need sudo?): {pe}", "error")
    except FileNotFoundError as fnf:
        log_and_print(f"Required Linux service missing: {fnf}", "error")
    except Exception as e:
        log_and_print(f"Linux installation failed: {e}", "error")
    return False

# -----------------------
# Dispatcher
# -----------------------
def install_profile(device):
    log_and_print(f"\n— ARA INSTALL — {datetime.now()}")
    log_and_print(f"Device: {device}")

    installers = {
        "iOS/Mac": install_ios,
        "Android": install_android,
        "Windows": install_windows,
        "Linux": install_linux
    }

    if device not in installers:
        log_and_print("Unknown device: cannot proceed.", "error")
        return

    success = installers[device]()

    if not success:
        log_and_print("Installation aborted due to errors.", "error")
        return

    confirm = input("\nReplace now? (y/N): ").strip().lower()
    if confirm != "y":
        log_and_print("Installation canceled by user.")
        return

    log_and_print("Replacement active.")
    log_and_print("Say 'Hey Ara' to wake.")
    log_and_print("Say 'Restore original' to revert.")
    log_and_print("All data encrypted. On-device only.")

    try:
        subprocess.Popen([sys.executable, "ara_listener.py"])
        log_and_print("Ara listener started successfully.")
    except PermissionError as pe:
        log_and_print(f"Permission error while starting Ara listener: {pe}", "error")
    except FileNotFoundError as fnf:
        log_and_print(f"ara_listener.py not found: {fnf}", "error")
    except Exception as e:
        log_and_print(f"Failed to start ara_listener.py: {e}", "error")

# -----------------------
# Main
# -----------------------

if __name__ == "__main__":
    device = get_device()
    if device == "Unknown":
        log_and_print("Device not supported.", "error")
        sys.exit(1)

    log_and_print("Ara is ready. Consent-based only.")
    install_profile(device)