import threading
import time
import uuid
import sys
import json
from pathlib import Path

from loggingutils.immutablelogger import ImmutableLogger


class SystemOrchestrator:
    """Main orchestrator for system initialization, boot handshake, and log monitoring."""

    def __init__(self, config_path: str = "config.json"):
        print("Loading configuration in strict mode...")

        # Load configuration
        self.config = self._load_config(config_path)

        # Initialize logger
        self.logger = ImmutableLogger(
            log_file=self.config.get("scarfile", "scar_chain.log")
        )

        # Assign a unique system ID
        self.system_id = str(uuid.uuid4())
        print(f"System ID: {self.system_id}")

        # Boot handshake
        if not self._boot_handshake():
            print("Boot handshake failed. Exiting.")
            sys.exit(1)

        # Start monitoring logs in a separate thread
        self.monitor_thread = threading.Thread(target=self._monitor_logs, daemon=True)
        self.monitor_thread.start()

        print("SystemOrchestrator initialized successfully")

    def _load_config(self, config_path: str) -> dict:
        """Load JSON configuration from the given path."""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        with open(path, encoding='utf-8') as f:
            return json.load(f)

    def _boot_handshake(self) -> bool:
        """Write boot entry to logs and verify integrity."""
        print("Writing boot entry...")
        success = self.logger.write_boot_entry(self.system_id)

        if success and self.logger.verify_integrity():
            print("Handshake successful - logs verified")
            return True

        print("Handshake failed - integrity check failed")
        return False

    def _monitor_logs(self):
        """Continuously verify log integrity in the background."""
        while True:
            if not self.logger.verify_integrity():
                print("Log integrity violated!")
                # Future: self.killswitch.activate("Integrity breach")
                break
            time.sleep(5)

    def execute(self, inputs: list):
        """Process a list of input strings and log output."""
        print("Starting execution phase...")
        for text in inputs:
            print(f"IN:  {text}")
            print(f"OUT: {text[:30]}... (cleaned)\n")
