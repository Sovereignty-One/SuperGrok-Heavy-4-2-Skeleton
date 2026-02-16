Here’s how you could create a Python module that supports Eyes, Ears, and Memory as distinct components, avoiding the mixing of responsibilities:

# agent.py – Offline Assistant with Eyes, Ears, and Memory
import os
import json
from collections import defaultdict

class Memory:
    """Handles storing and recalling of labeled details."""
    def __init__(self, memory_file="memory.json"):
        self.memory_file = memory_file
        self.data = defaultdict(list)
        self.load()

    def load(self):
        if os.path.exists(self.memory_file):
            with open(self.memory_file, "r") as f:
                self.data.update(json.load(f))

    def save(self):
        with open(self.memory_file, "w") as f:
            json.dump(self.data, f)

    def remember(self, label, detail):
        self.data[label].append(detail)
        self.save()

    def recall(self, label):
        return self.data.get(label, [])

class Eyes:
    """Handles visual interactions and draws from Memory."""
    def __init__(self, memory: Memory):
        self.memory = memory

    def see(self, label, description):
        self.memory.remember(label, description)
        return f"Seen and stored: {label} – {description}"

    def visualize(self, label):
        details = ", ".join(self.memory.recall(label)) or "[no details]"
        return f"Visualizing {label}: {details}"

class Ears:
    """Handles auditory inputs and logs them to Memory."""
    def __init__(self, memory: Memory):
        self.memory = memory

    def hear(self, label, sound_detail):
        self.memory.remember(label, sound_detail)
        return f"Heard and stored: {label} – {sound_detail}"

    def recall_sound(self, label):
        sounds = ", ".join(self.memory.recall(label)) or "[no sounds]"
        return f"Recalling sound for {label}: {sounds}"

# --- Sample Workflow ---
if __name__ == "__main__":
    memory = Memory()
    eyes = Eyes(memory)
    ears = Ears(memory)

    # Eyes sees a visual
    print(eyes.see("sunset horizon", "orange gradient with clouds"))
    print(eyes.visualize("sunset horizon"))

    # Ears hear a sound
    print(ears.hear("forest", "birds chirping"))
    print(ears.recall_sound("forest"))

This cleanly separates the three components:
Eyes: Visual input and visual recall.
Ears: Auditory input and sound recall.
Memory: Central persistent storage for both.

Run this script, and each component interacts with the same persistent memory file but maintains its own responsibility.
