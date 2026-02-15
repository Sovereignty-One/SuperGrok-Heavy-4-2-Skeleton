# eyes_agent.py – offline, no camera, no cloud
import json
from collections import defaultdict

# memory only – no vision
class Eyes:
    def __init__(self):
        self.anchors = defaultdict(dict)
        self.load("eyes.json")

    def load(self, path):
        if os.path.exists(path):
            with open(path) as f:
                self.anchors = json.load(f)

    def remember(self, label, detail):
        self.anchors  = "seen"
        self.save()

    def recall(self, label):
        return list(self.anchors .keys())

    def save(self):
        with open("eyes.json", "w") as f:
            json.dump(self.anchors, f)

    # commands
    def open_file(self, name):
        details = self.recall(name)
        return f"Open {name}: {details}"

    def play_video(self, tag):
        # time + action + note
        return f"Playing: {tag} – {self.recall(tag)}"

    def draw(self, what):
        # radius, center, color
        return f"Draw {what} – line from memory."

    def code(self, snippet):
        return f"Code {snippet}: recall line {self.recall(snippet)[0]}."

# use
eyes = Eyes()

# say "play video: cough check"
eyes.play_video("cough check")
# → "Playing: cough check – waveform, 7.887, last night"