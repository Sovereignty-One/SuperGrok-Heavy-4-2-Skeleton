class MemoryManager:
    def __init__(self, brain_state: dict):
        self.brain_state = brain_state

    def sanitize_expired_tokens(self, session_id: str):
        logs = self.brain_state.get("scarlog", [])
        cleaned = [log for log in logs if log.get("session_id") == session_id or log.get("type") == "user_learning"]
        self.brain_state["scarlog"] = cleaned[-50:]