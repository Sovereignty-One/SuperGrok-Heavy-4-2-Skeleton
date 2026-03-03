import json
import os

MEMORY_FILE = "memory.json"


class MemoryStore:
    def load(self):
        if not os.path.exists(MEMORY_FILE):
            return {}
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)

    def save(self, context):
        with open(MEMORY_FILE, "w") as f:
            json.dump(context, f, indent=2)