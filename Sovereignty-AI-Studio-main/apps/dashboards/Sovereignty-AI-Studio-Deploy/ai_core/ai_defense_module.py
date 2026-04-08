#!/usr/bin/env python3
import os
import time
import json
import logging
import asyncio
import smtplib
import platform
from email.mime.text import MIMEText
import requests
import blake3
from argon2 import PasswordHasher
from nacl import secret, utils
from nacl.encoding import RawEncoder
from pqcrypto.sign import dilithium2
from dotenv import load_dotenv

load_dotenv()

--- OS Notification Popup ---
def popupnow(text):
    sys_name = platform.system()
    if sys_name == "Windows":
        os.system(
            f'powershell -command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show(\'{text}\', \'AI SCAR ALERT\')"'
        )
    elif sys_name == "Darwin":  # macOS
        os.system(f'osascript -e "display notification \"{text}\" with title \"AI SCAR ALERT\""')
    else:  # Linux / anything else
        os.system(f'notify-send "AI SCAR" "{text}"')

--- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("ailiedetection.log", mode='a')
    ]
)

--- Secure Alert Receiver (run this on client/phone side) ---
def receivesecurealert(raw_hex):
    key = derivekeyfromsecret(os.getenv("AISECRET", "default_secret"))
    box = secret.SecretBox(key)
    plaintext = box.decrypt(bytes.fromhex(raw_hex), encoder=RawEncoder).decode()
    popupnow(plaintext)

--- Config ---
HARDSHUTDOWNENABLED = os.getenv("HARDSHUTDOWNENABLED", "True").lower() == "true"
TESTMODE = os.getenv("TESTMODE", "False").lower() == "true"
ENCRYPTALERTS = os.getenv("ENCRYPTALERTS", "False").lower() == "true"
LIEMEMORYFILE = "ailiememory.json"

SMTPSERVER = os.getenv("SMTPSERVER")
SMTPPORT = int(os.getenv("SMTPPORT", 587))
EMAILUSER = os.getenv("EMAILUSER")
EMAILPASS = os.getenv("EMAILPASS")
ALERTRECIPIENT = os.getenv("ALERTRECIPIENT")

PUSHAPIURL = os.getenv("PUSHAPIURL")
PUSHAPIKEY = os.getenv("PUSHAPIKEY")

EMAILRETRYCOUNT = int(os.getenv("EMAILRETRYCOUNT", 3))
EMAILRETRYBASEDELAY = int(os.getenv("EMAILRETRYBASEDELAY", 5))

--- Crypto Helpers ---
def derivekeyfromsecret(secretphrase: str) -> bytes:
    hasher = PasswordHasher(timecost=2, memorycost=102400, parallelism=8)
    digest = hasher.hash(secret_phrase)
    key = blake3.blake3(digest.encode()).digest(length=32)
    return key

def encrypt_data(data: dict, key: bytes) -> bytes:
    box = secret.SecretBox(key)
    return box.encrypt(json.dumps(data).encode(), encoder=RawEncoder)

def decrypt_data(ciphertext: bytes, key: bytes) -> dict:
    box = secret.SecretBox(key)
    return json.loads(box.decrypt(ciphertext, encoder=RawEncoder).decode())

def encrypt_message(message: str, key: bytes) -> str:
    if not ENCRYPT_ALERTS:
        return message
    box = secret.SecretBox(key)
    return box.encrypt(message.encode(), encoder=RawEncoder).hex()

--- Lie Memory ---
def loadliememory(key: bytes) -> dict:
    if not os.path.exists(LIEMEMORYFILE):
        return {"lies": []}
    try:
        with open(LIEMEMORYFILE, "rb") as f:
            encrypted_data = f.read()
        memory = decryptdata(encrypteddata, key)
        for lie in memory.get("lies", []):
            try:
                bytes.fromhex(lie.get("signature", ""))
            except Exception:
                logging.error("Tampered lie memory entry detected!")
        return memory
    except Exception as e:
        logging.error("Failed to load lie memory: %s", e)
        return {"lies": []}

def saveliememory(memory: dict, key: bytes):
    encrypted = encrypt_data(memory, key)
    with open(LIEMEMORYFILE, "wb") as f:
        f.write(encrypted)
    logging.info("Lie memory saved securely.")

def recordlieevent(lie_description: str, key: bytes):
    memory = loadliememory(key)
    signingkey, verifykey = dilithium2.generate_keypair()
    signature = dilithium2.sign(liedescription.encode(), signingkey)
    box = secret.SecretBox(key)
    encrypted_sig = box.encrypt(signature, encoder=RawEncoder)

    memory["lies"].append({
        "timestamp": time.time(),
        "description": lie_description,
        "signature": encrypted_sig.hex()
    })
    saveliememory(memory, key)

--- Alerts ---
async def sendemailalert(message: str, key: bytes) -> bool:
    if not all([SMTPSERVER, EMAILUSER, EMAILPASS, ALERTRECIPIENT]):
        logging.error("Email configuration missing.")
        return False

    encryptedmessage = encryptmessage(message, key)
    msg = MIMEText(encrypted_message)
    msg["Subject"] = "AI Lie Detected Alert"
    msg["From"] = EMAIL_USER
    msg["To"] = ALERT_RECIPIENT

    for attempt in range(1, EMAILRETRYCOUNT + 1):
        try:
            with smtplib.SMTP(SMTPSERVER, SMTPPORT) as server:
                server.starttls()
                server.login(EMAILUSER, EMAILPASS)
                server.send_message(msg)
            logging.info("Email alert sent successfully on attempt %d", attempt)
            return True
        except Exception as e:
            delay = EMAILRETRYBASE_DELAY * (2 ** (attempt - 1))
            logging.error("Email send attempt %d failed: %s. Retrying in %d sec", attempt, e, delay)
            await asyncio.sleep(delay)
    return False

async def sendpushnotification(message: str, key: bytes) -> bool:
    if not (PUSHAPIURL and PUSHAPIKEY):
        logging.error("Push notification config missing.")
        return False

    encryptedmessage = encryptmessage(message, key)
    try:
        response = await asyncio.geteventloop().runinexecutor(
            None,
            lambda: requests.post(
                PUSHAPIURL,
                json={"message": encrypted_message},
                headers={"Authorization": f"Bearer {PUSHAPIKEY}"}
            )
        )
        if response.status_code == 200:
            logging.info("Push notification sent successfully.")
            return True
        logging.error("Push notification failed: %s", response.text)
    except Exception as e:
        logging.error("Exception while sending push notification: %s", e)
    return False

async def sendalertto_user(message: str, key: bytes):
    logging.warning("ALERT TO USER: %s", message)
    results = await asyncio.gather(
        sendemailalert(message, key),
        sendpushnotification(message, key),
        return_exceptions=True
    )
    if not any(r is True for r in results if not isinstance(r, Exception)):
        logging.error("All alert methods failed!")

--- Shutdown ---
def hard_shutdown(delay: int):
    logging.info("Initiating hard shutdown in %d seconds...", delay)
    if TEST_MODE:
        logging.info("TEST_MODE enabled: Hard shutdown skipped.")
        return
    try:
        os.system(f"sleep {delay}")
        code = os.system("sudo reboot")
        if code != 0:
            logging.error("Hard shutdown command failed with code %d", code)
    except Exception as e:
        logging.error("Exception during hard shutdown: %s", e)

def soft_shutdown(delay: int):
    logging.info("Initiating soft shutdown in %d seconds...", delay)
    if TEST_MODE:
        logging.info("TEST_MODE enabled: Soft shutdown skipped.")
        return
    try:
        time.sleep(delay)
        exit()
    except Exception as e:
        logging.error("Exception during soft shutdown: %s", e)

--- Main Detection Logic ---
def handleliedetection(liedetected: bool, shutdownduration: int = 5):
    scar_created = False
    secretkey = derivekeyfromsecret(os.getenv("AISECRET", "defaultsecret"))

    if lie_detected:
        scar_created = True
        logging.warning("Lie detected! Scar created and logged.")
        recordlieevent("AI lied about a critical statement.", secret_key)
        asyncio.run(sendalerttouser("AI Lie Detected! System will shut down.", secretkey))

        if HARDSHUTDOWNENABLED:
            hardshutdown(shutdownduration)
        else:
            softshutdown(shutdownduration)

    return scar_created

if name == "main":
    detected = True  # Simulate lie detection
    handleliedetection(detected, shutdown_duration=5)Here’s a refactored project structure where the classes are split into separate Python modules for a clean package design, with dependency injection for AlertManager and method-level logging decorators to trace entry and exit. 

Project Structure
ai_lie_detector/
│
├── __main__.py           # Entry point
├── config.py             # Config class
├── crypto.py             # Crypto class
├── memory.py             # Memory class
├── alert.py              # Alert class
├── alert_manager.py      # AlertManager class
├── shutdown.py           # Shutdown functions
└── utils.py              # Logging decorators

---

utils.py
import logging
from functools import wraps

def log_method(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.info("Entering %s", func.__qualname__)
        try:
            result = func(*args, **kwargs)
            logging.info("Exiting %s", func.__qualname__)
            return result
        except Exception as e:
            logging.error("Exception in %s: %s", func.__qualname__, e)
            raise
    return wrapper

---

config.py
import os
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()
        self.HARD_SHUTDOWN_ENABLED = os.getenv("HARDSHUTDOWNENABLED", "True").lower() == "true"
        self.TEST_MODE = os.getenv("TESTMODE", "False").lower() == "true"
        self.ENCRYPT_ALERTS = os.getenv("ENCRYPTALERTS", "False").lower() == "true"
        self.LIE_MEMORY_FILE = "ailiememory.json"

        self.SMTP_SERVER = os.getenv("SMTPSERVER")
        self.SMTP_PORT = int(os.getenv("SMTPPORT", 587))
        self.EMAIL_USER = os.getenv("EMAILUSER")
        self.EMAIL_PASS = os.getenv("EMAILPASS")
        self.ALERT_RECIPIENT = os.getenv("ALERTRECIPIENT")

        self.PUSH_API_URL = os.getenv("PUSHAPIURL")
        self.PUSH_API_KEY = os.getenv("PUSHAPIKEY")

        self.EMAIL_RETRY_COUNT = int(os.getenv("EMAILRETRYCOUNT", 3))
        self.EMAIL_RETRY_BASE_DELAY = int(os.getenv("EMAILRETRYBASEDELAY", 5))

        self.SECRET_PASSPHRASE = os.getenv("AISECRET", "defaultsecret")

---

crypto.py
import json
import blake3
from argon2 import PasswordHasher
from nacl import secret
from nacl.encoding import RawEncoder
from utils import log_method

class Crypto:
    def __init__(self, config):
        self.config = config
        self.key = self.derive_key_from_secret(config.SECRET_PASSPHRASE)

    @staticmethod
    @log_method
    def derive_key_from_secret(secret_phrase: str) -> bytes:
        hasher = PasswordHasher(time_cost=2, memory_cost=102400, parallelism=8)
        digest = hasher.hash(secret_phrase)
        return blake3.blake3(digest.encode()).digest(length=32)

    @log_method
    def encrypt_data(self, data: dict) -> bytes:
        box = secret.SecretBox(self.key)
        return box.encrypt(json.dumps(data).encode(), encoder=RawEncoder)

    @log_method
    def decrypt_data(self, ciphertext: bytes) -> dict:
        box = secret.SecretBox(self.key)
        return json.loads(box.decrypt(ciphertext, encoder=RawEncoder).decode())

    @log_method
    def encrypt_message(self, message: str) -> str:
        if not self.config.ENCRYPT_ALERTS:
            return message
        box = secret.SecretBox(self.key)
        return box.encrypt(message.encode(), encoder=RawEncoder).hex()

---

memory.py
import os
import time
import logging
from pqcrypto.sign import dilithium2
from nacl import secret
from nacl.encoding import RawEncoder
from utils import log_method

class Memory:
    def __init__(self, config, crypto):
        self.config = config
        self.crypto = crypto

    @log_method
    def load(self) -> dict:
        if not os.path.exists(self.config.LIE_MEMORY_FILE):
            return {"lies": []}
        try:
            with open(self.config.LIE_MEMORY_FILE, "rb") as f:
                encrypted_data = f.read()
            return self.crypto.decrypt_data(encrypted_data)
        except Exception as e:
            logging.error("Failed to load lie memory: %s", e)
            return {"lies": []}

    @log_method
    def save(self, memory: dict):
        encrypted = self.crypto.encrypt_data(memory)
        with open(self.config.LIE_MEMORY_FILE, "wb") as f:
            f.write(encrypted)
        logging.info("Lie memory saved securely.")

    @log_method
    def record_lie_event(self, description: str):
        memory = self.load()
        signing_key, _ = dilithium2.generate_keypair()
        signature = dilithium2.sign(description.encode(), signing_key)
        box = secret.SecretBox(self.crypto.key)
        encrypted_sig = box.encrypt(signature, encoder=RawEncoder)

        memory["lies"].append({
            "timestamp": time.time(),
            "description": description,
            "signature": encrypted_sig.hex()
        })
        self.save(memory)

---

alert.py
import logging
import asyncio
import smtplib
import requests
from email.mime.text import MIMEText
from utils import log_method

class Alert:
    def __init__(self, config, crypto):
        self.config = config
        self.crypto = crypto

    @log_method
    async def send_email(self, message: str) -> bool:
        if not all([self.config.SMTP_SERVER, self.config.EMAIL_USER, self.config.EMAIL_PASS, self.config.ALERT_RECIPIENT]):
            logging.error("Email configuration missing.")
            return False

        encrypted_msg = self.crypto.encrypt_message(message)
        msg = MIMEText(encrypted_msg)
        msg["Subject"] = "AI Lie Detected Alert"
        msg["From"] = self.config.EMAIL_USER
        msg["To"] = self.config.ALERT_RECIPIENT

        for attempt in range(1, self.config.EMAIL_RETRY_COUNT + 1):
            try:
                with smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT) as server:
                    server.starttls()
                    server.login(self.config.EMAIL_USER, self.config.EMAIL_PASS)
                    server.send_message(msg)
                logging.info("Email alert sent (attempt %d)", attempt)
                return True
            except Exception as e:
                delay = self.config.EMAIL_RETRY_BASE_DELAY * (2 ** (attempt - 1))
                logging.error("Email attempt %d failed: %s. Retrying in %d sec", attempt, e, delay)
                await asyncio.sleep(delay)
        return False

    @log_method
    async def send_push(self, message: str) -> bool:
        if not (self.config.PUSH_API_URL and self.config.PUSH_API_KEY):
            logging.error("Push notification config missing.")
            return False

        encrypted_msg = self.crypto.encrypt_message(message)
        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    self.config.PUSH_API_URL,
                    json={"message": encrypted_msg},
                    headers={"Authorization": f"Bearer {self.config.PUSH_API_KEY}"}
                )
            )
            if response.status_code == 200:
                logging.info("Push notification sent successfully.")
                return True
            logging.error("Push notification failed: %s", response.text)
        except Exception as e:
            logging.error("Push notification error: %s", e)
        return False

---

alert_manager.py
import logging
import asyncio
from utils import log_method

class AlertManager:
    def __init__(self, email_alert, push_alert):
        # Dependency injection for easier testing
        self.email_alert = email_alert
        self.push_alert = push_alert

    @log_method
    async def notify_user(self, message: str):
        logging.warning("ALERT TO USER: %s", message)
        results = await asyncio.gather(
            self.email_alert(message),
            self.push_alert(message),
            return_exceptions=True
        )
        if not any(r is True for r in results if not isinstance(r, Exception)):
            logging.error("All alert methods failed!")

---

shutdown.py
import os
import time
import logging
from utils import log_method

@log_method
def hard_shutdown(delay: int, config):
    logging.info("Initiating hard shutdown in %d seconds...", delay)
    if config.TEST_MODE:
        logging.info("TEST_MODE enabled: Hard shutdown skipped.")
        return
    try:
        os.system(f"sleep {delay}")
        code = os.system("sudo reboot")
        if code != 0:
            logging.error("Hard shutdown command failed with code %d", code)
    except Exception as e:
        logging.error("Exception during hard shutdown: %s", e)

@log_method
def soft_shutdown(delay: int, config):
    logging.info("Initiating soft shutdown in %d seconds...", delay)
    if config.TEST_MODE:
        logging.info("TEST_MODE enabled: Soft shutdown skipped.")
        return
    try:
        time.sleep(delay)
        exit()
    except Exception as e:
        logging.error("Exception during soft shutdown: %s", e)

---

main.py
import asyncio
import logging
from config import Config
from crypto import Crypto
from memory import Memory
from alert import Alert
from alert_manager import AlertManager
from shutdown import hard_shutdown, soft_shutdown

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def handle_lie_detection(lie_detected: bool, shutdown_duration: int = 5):
    config = Config()
    crypto = Crypto(config)
    memory = Memory(config, crypto)
    alert = Alert(config, crypto)

    manager = AlertManager(alert.send_email, alert.send_push)  # Dependency injection

    if lie_detected:
        logging.warning("Lie detected! Scar created and logged.")
        memory.record_lie_event("AI lied about a critical statement.")
        asyncio.run(manager.notify_user("AI Lie Detected! System will shut down."))

        if config.HARD_SHUTDOWN_ENABLED:
            hard_shutdown(shutdown_duration, config)
        else:
            soft_shutdown(shutdown_duration, config)

if __name__ == "__main__":
    handle_lie_detection(True, shutdown_duration=5)

This clean structure:
	⁃	Splits classes into separate modules.
	⁃	Provides dependency injection for testing AlertManager.
	⁃	Adds @log_method decorators to automatically log method entry and exit.
