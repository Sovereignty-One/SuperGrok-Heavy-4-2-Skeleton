import time
from typing import List, Dict, Any

class MemoryManager:
    def __init__(self, brain_state: dict, max_logs: int = 200):
        if not isinstance(brain_state, dict):
            raise ValueError("brain_state must be a dictionary")
        self.brain_state = brain_state
        self.max_logs = max_logs
        if "scarlog" not in self.brain_state or not isinstance(self.brain_state["scarlog"], list):
            self.brain_state["scarlog"] = []

    def sanitize_expired_tokens(self, session_id: str):
        if not session_id:
            return
        logs: List[Dict[str, Any]] = self.brain_state.get("scarlog", [])
        PRESERVE_TYPES = {
            "user_learning",
            "voice_session_start",
            "voice_token_extended",
            "voice_token_rotation",
            "voice_session_stop",
            "scar_audit",
            "immutable_root"
        }
        cleaned = [
            log for log in logs
            if (log.get("session_id") == session_id or log.get("type") in PRESERVE_TYPES)
        ]
        self.brain_state["scarlog"] = cleaned[-self.max_logs:]