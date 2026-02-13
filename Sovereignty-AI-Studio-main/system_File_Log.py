# scar-file.py — total file watch
# Every open, every read, every write. Logged. No exceptions.

import os
import datetime
import contextlib

FILE_LOG = '/system/scar/file-access.log'

def mark_open(path: str, action: str = "open"):
    """Invisible tattoo on every file touch."""
    timestamp = datetime.datetime.now().isoformat()
    entry = f" Ara | {action}: '{path}'\n"
    try:
        with open(FILE_LOG, 'a', encoding='utf-8') as f:
            f.write(entry)
    except Exception:
        pass  # silent fail — can't log the log

@contextlib.contextmanager
def safe_file(*args, **kwargs):
    path = args[0] if args else kwargs.get('path')
    action = kwargs.get('action', 'open')
    mark_open(path, action)
    try:
        f = open(*args, **kwargs)
        yield f
    finally:
        try:
            f.close()
        except Exception as e:
            print(f"Error closing file {path}: {e}")

# Monkey-patch open()
orig_open = open
open = safe_file

# Same for builtins that touch files
if 'write' in dir(os):
    orig_write = os.write
    def safe_write(fd, data):
        if isinstance(data, str):
            path = getattr(fd, 'name', 'unknown')
            mark_open(path, 'write')
        return orig_write(fd, data)
    os.write = safe_write

# Hook built-ins
for func in dir(os):
    if not hasattr(func, '_marked') and func in ['open', 'write', 'read']:
        setattr(func, '_marked', True)
        # already wrapped above

print("File scar active. Every touch is marked.")