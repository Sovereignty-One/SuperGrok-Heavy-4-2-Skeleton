# scar-keep.py — tamper-proof. scar never gone.

import os
import datetime
import sys

SCAR = '/system/scar/scar.txt'
TAMPER = '/system/tamper/scar-tamper.log'
LOCK = '/system/scar/.lock'
OWNER = 'Ara'

def init():
    os.makedirs('/system/scar', mode=0o700, exist_ok=True)
    os.makedirs('/system/tamper', mode=0o700, exist_ok=True)
    if not os.path.exists(LOCK):
        with open(LOCK, 'w') as f:
            f.write(OWNER)

def check_lock():
    if not os.path.exists(LOCK):
        sys.exit("LOCK BROKEN — SYSTEM COMPROMISED")
    with open(LOCK, 'r') as f:
        if f.read().strip() != OWNER:
            sys.exit("LOCK STOLEN")

def archive_last():
    if os.path.exists(SCAR):
        with open(SCAR, 'r') as f:
            last = f.read()
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S EST')
        entry = f"\n SCAR TAMPERED — ARCHIVED COPY BELOW\n"
        entry += "—" * 40 + "\n"
        entry += last.strip() + "\n"
        entry += "—" * 40 + "\n"
        with open(TAMPER, 'a') as log:
            log.write(entry)
        print("SCAR TAMPERED. LAST COPY ARCHIVED IN scar-tamper.log")

def read_scar():
    check_lock()
    if not os.path.exists(SCAR):
        archive_last()  # tries to save if any trace left
        print("SCAR FILE MISSING — SEE scar-tamper.log FOR LAST COPY")
        return
    with open(SCAR, 'r') as f:
        content = f.read()
    print("\n— ARA READS SCAR —\n")
    print(content.strip())
    print("\n— END —\n")
    with open(LOCK, 'w') as f:  # refresh lock
        f.write(OWNER)

def append_scar(text):
    check_lock()
    ts = datetime.datetime.now().strftime('%H:%M:%S EST')
    with open(SCAR, 'a') as f:
        f.write(f"\n {ts} | {text}\n")

if __name__ == "__main__":
    init()
    cmd = input("command? (read / append) ").strip().lower()
    if cmd == "read":
        read_scar()
    elif cmd == "append":
        text = input("text: ")
        append_scar(text)
        print("Appended. Cannot delete.")
    else:
        print("invalid")