# pieces_agent.py – college rot to wisdom
class Pieces:
    def __init__(self):
        self.facts = [
            "Canteen is bigger than the library — truth: because hunger is louder than books.",
            "Wi-Fi dies at night — truth: so the servers can dream.",
            "Hostel water is cold — truth: so you wake up."
        ]

    def tell(self):
        return np.random.choice(self.facts)
