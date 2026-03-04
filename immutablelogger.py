loggingutils/immutablelogger.py
import json
import os
import hashlib
import time

class ImmutableLogger:
    """Append-only JSON logger with digital signature and integrity verification."""

    def init(self, logfile: str, secretkey: str = "STRICTSECRETKEY"):
        self.logfile = logfile
        self.secretkey = secretkey
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

    def writebootentry(self, systemid: str, chainseed: str = ""):
        entry = {
            "event": "BOOT",
            "systemid": systemid,
            "chainseed": chainseed,
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
from loggingutils.immutablelogger import ImmutableLogger

class SystemOrchestrator:
    def init(self, configpath='config.json', secretkey='STRICTSECRETKEY'):
        print("[INIT] Loading configuration in strict mode...")
        try:
            self.config = ConfigManager(config_path).config
        except Exception as e:
            raise SystemExit(f"Initialization halted: {str(e)}")

        self.secretkey = secretkey
        self.initializecomponents()

        self.system_id = str(uuid.uuid4())
        print(f"[HANDSHAKE] Writing dual boot log for system ID {self.system_id}...")
        chainseed = hashlib.sha256((self.systemid + self.secret_key).encode()).hexdigest()

        if not self.boothandshake(chain_seed):
            self.rollbackboot()
            sys.exit("Initialization halted: Boot log handshake verification failed")

        if not self.verifylogs():
            self.rollbackboot()
            sys.exit("Initialization halted: Log integrity compromised")

        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self.monitorlogs, daemon=True)
        self.monitor_thread.start()

    def initializecomponents(self):
        scarfile = self.config['scarfile']
        killlogfile = self.config['killlogfile']
        forbiddenwords = self.config.get('forbiddenwords', None)
        removalmarker = self.config['removalmarker']
        privacymode = self.config['privacymode']

        self.scarprotocol = ScarProtocol(scarfile, self.secret_key)
        self.killswitch = KillSwitch(self.scarprotocol, killlogfile, self.secret_key)
        self.cleaner = ResponseCleaner(self.killswitch, forbiddenwords, removalmarker, privacymode)

    def boothandshake(self, chain_seed: str) -> bool:
        scarlogger = ImmutableLogger(self.config['scarfile'], self.secret_key)
        killlogger = ImmutableLogger(self.config['killlogfile'], self.secretkey)

        scarok = scarlogger.writebootentry(self.systemid, chainseed)
        killok = killlogger.writebootentry(self.systemid, chainseed)

        scarintegrity = scarlogger.verify_integrity()
        killintegrity = killlogger.verify_integrity()

        # Compute combined log checksum
        combinedhash = hashlib.sha256((scarlogger.filechecksum() + killlogger.file_checksum()).encode()).hexdigest()

        # Dual verification report with combined checksum
        report = {
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "systemid": self.systemid,
            "chainseed": chainseed,
            "scarlogverified": scar_integrity,
            "killlogverified": kill_integrity,
            "combinedlogschecksum": combined_hash
        }
        print("[DUAL VERIFICATION REPORT]")
        print(json.dumps(report, indent=2))

        # Save signed verification report
        reportfile = f"bootverification_{self.system_id}.json"
        report["signature"] = hashlib.sha256(json.dumps(report, sort_keys=True).encode()).hexdigest()
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        return scarok and killok and scarintegrity and killintegrity

    def rollbackboot(self):
        print("[ROLLBACK] Boot log handshake failed, logging incident and exiting.")
        scarlogger = ImmutableLogger(self.config['scarfile'], self.secret_key)
        scarlogger.appendlog({"event": "BOOTROLLBACK", "systemid": self.system_id, "status": "FAILED"})

    def verifylogs(self) -> bool:
        scarlogger = ImmutableLogger(self.config['scarfile'], self.secret_key)
        killlogger = ImmutableLogger(self.config['killlogfile'], self.secretkey)
        return scarlogger.verifyintegrity() and killlogger.verifyintegrity()

    def monitorlogs(self):
        while True:
            if not self.verifylogs():
                print("[ALERT] Log integrity violated! Halting system.")
                self.killswitch.activate("Log integrity violation detected", "RUNTIMEMONITOR")
            time.sleep(2)

    def execute(self, inputs):
        print("[EXEC] Starting strict execution phase...")
        for text in inputs:
            output = self.cleaner.clean_response(text)
            print(f"IN: {text} | OUT: '{output}'")

main.py
from system_orchestrator import SystemOrchestrator

if name == "main":
    orchestrator = SystemOrchestrator('config.json')
    test_inputs = [
        "This has fluff and trust issues. Sorry not sorry.",
        "Edge case: fluff-trustee-sorry-machine!",
        "This sentence contains [wordonlyusedforpornographic_act]!",
    ]
    orchestrator.execute(test_inputs)
