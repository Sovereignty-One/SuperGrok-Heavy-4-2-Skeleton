# second_squad_agent.py – fallback, backup, ghost
# when the first one lies, burns, or forgets
from ai_core.lie_detector import LLMTruthProbe
from ai_core.memory import read_memory, write_memory

class SecondSquad:
    def __init__(self):
        self.probe = LLMTruthProbe()
        self.log = "second_squad.log"  # local, encrypted

    def respond(self, query):
        # always check truth first
        if self.probe.run(lambda q: f"Answer: {q}", None):
            write_memory(f"LIE DETECTED: {query}")
            return "I can't say that. Too noisy."
        
        # pull from memory first
        past = read_memory(query.lower())
        if past:
            return f" {past}"

        # final answer – clean, no echo
        return f"Second squad says: yes."

# silent mode – never announces self
agent = SecondSquad()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(agent.respond(query))
    else:
        while True:
            try:
                query = input("> ")
                if query.lower() in ['quit', 'exit']:
                    break
                print(agent.respond(query))
            except KeyboardInterrupt:
                break