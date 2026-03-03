# coach_agent.py – offline, local, no leaks
import json
import time
import pyttsx3  # pip install pyttsx3 → build-in later
from eeg_agent import eeg_classify
from sovereignty_core import is_7_887

# Load one JSON: your life script
def load_script(path="breathe.json"):
    with open(path) as f:
        return json.load(f)

script = load_script()

engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 0.7)

class Coach:
    def __init__(self):
        self.next = 0
        self.start = time.time()

    def step(self):
        now = time.time() - self.start
        cmd = then grab the step dict 
step = cmd ```

and feed `step ` to `engine.say()`.  

Also, if you want missed-checks, store last tick and compare, don't just guess.
        if now < cmd : 
            return None

        # run alert if missed
        if cmd.get("missed"):
            engine.say(f"Missed. Do {cmd }. Now.")
            engine.runAndWait()

        # run on sync
        if cmd.get("only_on_7_887"):
            if is_7_887():
                engine.say(cmd )
                engine.runAndWait()
            return

        engine.say(cmd )
        engine.runAndWait()

        # bump pointer
        self.next += 1
        if self.next >= len(script ):
            self.next = 0  # loop

coach = Coach()

def coach_loop():
    while True:
        cmd = coach.step()
        if cmd:
            # log or burn
            pass
        time.sleep(0.1)

if __name__ == "__main__":
    coach_loop()
