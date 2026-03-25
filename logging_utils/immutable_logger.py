#logging_utils/immutable_logger.py

import json
import os
import hashlib
import time

class ImmutableLogger:
“”“Append-only JSON logger with digital signature and integrity verification.”””

def __init__(self, log_file: str, secret_key: str = "STRICT_SECRET_KEY"):
    self.log_file = log_file
    self.secret_key = secret_key
    if not os.path.exists(self.log_file):
        with open(self.log_file, 'w', encoding='utf-8') as f:
            pass

def _sign(self, data: dict) -> str:
    payload = json.dumps(data, sort_keys=True)
    return hashlib.sha256((payload + self.secret_key).encode()).hexdigest()

def append_log(self, data: dict):
    timestamp = time.time()
    data["timestamp"] = timestamp
    data["signature"] = self._sign(data)
    with open(self.log_file, 'a', encoding='utf-8') as f:
        json.dump(data, f)
        f.write('\n')

def verify_integrity(self) -> bool:
    try:
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                entry = json.loads(line)
                signature = entry.pop("signature", None)
                expected = self._sign(entry)
                if signature != expected:
                    return False
        return True
    except:
        return False

def write_boot_entry(self, system_id: str, chain_seed: str = ""):
    entry = {
        "event": "BOOT",
        "system_id": system_id,
        "chain_seed": chain_seed,
        "status": "BOOT_OK"
    }
    self.append_log(entry)
    return self.verify_integrity()

def file_checksum(self) -> str:
    sha = hashlib.sha256()
    with open(self.log_file, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha.update(chunk)
    return sha.hexdigest()

system_orchestrator.py

import threading
import time
import uuid
import hashlib
import sys
import json
from datetime import datetime
from scar_protocol import ScarProtocol
from kill_switch import KillSwitch
from response_cleaner import ResponseCleaner
from config_manager import ConfigManager
from logging_utils.immutable_logger import ImmutableLogger

class SystemOrchestrator:
def init(self, config_path=‘config.json’, secret_key=‘STRICT_SECRET_KEY’):
print(”[INIT] Loading configuration in strict mode…”)
try:
self.config = ConfigManager(config_path).config
except Exception as e:
raise SystemExit(f”Initialization halted: {str(e)}”)

    self.secret_key = secret_key
    self._initialize_components()

    self.system_id = str(uuid.uuid4())
    print(f"[HANDSHAKE] Writing dual boot log for system ID {self.system_id}...")
    chain_seed = hashlib.sha256((self.system_id + self.secret_key).encode()).hexdigest()

    if not self._boot_handshake(chain_seed):
        self._rollback_boot()
        sys.exit("Initialization halted: Boot log handshake verification failed")

    if not self._verify_logs():
        self._rollback_boot()
        sys.exit("Initialization halted: Log integrity compromised")

    # Start monitoring thread
    self.monitor_thread = threading.Thread(target=self._monitor_logs, daemon=True)
    self.monitor_thread.start()

def _initialize_components(self):
    scar_file = self.config['scar_file']
    kill_log_file = self.config['kill_log_file']
    forbidden_words = self.config.get('forbidden_words', None)
    removal_marker = self.config['removal_marker']
    privacy_mode = self.config['privacy_mode']

    self.scar_protocol = ScarProtocol(scar_file, self.secret_key)
    self.kill_switch = KillSwitch(self.scar_protocol, kill_log_file, self.secret_key)
    self.cleaner = ResponseCleaner(self.kill_switch, forbidden_words, removal_marker, privacy_mode)

def _boot_handshake(self, chain_seed: str) -> bool:
    scar_logger = ImmutableLogger(self.config['scar_file'], self.secret_key)
    kill_logger = ImmutableLogger(self.config['kill_log_file'], self.secret_key)

    scar_ok = scar_logger.write_boot_entry(self.system_id, chain_seed)
    kill_ok = kill_logger.write_boot_entry(self.system_id, chain_seed)

    scar_integrity = scar_logger.verify_integrity()
    kill_integrity = kill_logger.verify_integrity()

    # Compute combined log checksum
    combined_hash = hashlib.sha256((scar_logger.file_checksum() + kill_logger.file_checksum()).encode()).hexdigest()

    # Dual verification report with combined checksum
    report = {
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "system_id": self.system_id,
        "chain_seed": chain_seed,
        "scar_log_verified": scar_integrity,
        "kill_log_verified": kill_integrity,
        "combined_logs_checksum": combined_hash
    }
    print("[DUAL VERIFICATION REPORT]")
    print(json.dumps(report, indent=2))

    # Save signed verification report
    report_file = f"boot_verification_{self.system_id}.json"
    report["signature"] = hashlib.sha256(json.dumps(report, sort_keys=True).encode()).hexdigest()
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    return scar_ok and kill_ok and scar_integrity and kill_integrity

def _rollback_boot(self):
    print("[ROLLBACK] Boot log handshake failed, logging incident and exiting.")
    scar_logger = ImmutableLogger(self.config['scar_file'], self.secret_key)
    scar_logger.append_log({"event": "BOOT_ROLLBACK", "system_id": self.system_id, "status": "FAILED"})

def _verify_logs(self) -> bool:
    scar_logger = ImmutableLogger(self.config['scar_file'], self.secret_key)
    kill_logger = ImmutableLogger(self.config['kill_log_file'], self.secret_key)
    return scar_logger.verify_integrity() and kill_logger.verify_integrity()

def _monitor_logs(self):
    while True:
        if not self._verify_logs():
            print("[ALERT] Log integrity violated! Halting system.")
            self.kill_switch.activate("Log integrity violation detected", "RUNTIME_MONITOR")
        time.sleep(2)

def execute(self, inputs):
    print("[EXEC] Starting strict execution phase...")
    for text in inputs:
        output = self.cleaner.clean_response(text)
        print(f"IN: {text} | OUT: '{output}'")

main.py

from system_orchestrator import SystemOrchestrator

if name == “main”:
orchestrator = SystemOrchestrator(‘config.json’)
test_inputs = [
“This has fluff and trust issues. Sorry not sorry.”,
“Edge case: fluff-trustee-sorry-machine!”,
“This sentence contains [wordonlyusedforpornographic_act]!”,
]
orchestrator.execute(test_inputs)
