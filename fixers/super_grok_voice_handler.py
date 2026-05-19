import json
import time
import asyncio
import secrets
from fixers.persist_brain import persist_brain
from fixers.handle_error import handle_error
from fixers.rate_limiter import RateLimiter
from fixers.memory_manager import MemoryManager

class SuperGrokVoiceHandler:
    def __init__(self, brain_state: dict, user_tier: str = "SUPERGROK"):
        if not isinstance(brain_state, dict) or "state" not in brain_state:
            raise ValueError("brain_state must be a dict containing 'state' key")
        self.brain_state = brain_state
        self.user_tier = user_tier.upper()
        self.session_id = None
        self.token_count = 0
        self.turn_count = 0
        self.last_rotation = time.time()
        if self.user_tier == "SUPERGROK":
            self.base_limit = 16384
            self.extend_by = 8192
        elif self.user_tier == "HEAVY":
            self.base_limit = 65536
            self.extend_by = 32768
        else:
            self.base_limit = 4096
            self.extend_by = 2048
        self.max_tokens = self.base_limit
        self.rate_limiter = RateLimiter(max_requests=60, window_seconds=60)
        self.memory_manager = MemoryManager(brain_state)
        self._rotation_task = None

    async def __aenter__(self):
        result = self.start_session()
        if result.get("status") != "active":
            raise RuntimeError(f"Failed to start voice session: {result}")
        self._rotation_task = asyncio.create_task(self._auto_audit_heartbeat())
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False

    def start_session(self) -> dict:
        if self.session_id:
            return {"status": "already_active", "session_id": self.session_id}
        self.session_id = f"voice-{secrets.token_hex(8)}-{self.user_tier}"
        self.token_count = 0
        self.turn_count = 0
        persist_brain(self.brain_state["state"], new_logs=[{"type": "voice_session_start", "session_id": self.session_id, "tier": self.user_tier, "base_limit": self.base_limit}])
        return {"status": "active", "session_id": self.session_id, "max_tokens": self.max_tokens, "message": f"SuperGrok voice ready • {self.max_tokens} tokens"}

    async def add_tokens(self, tokens_used: int) -> dict:
        if not self.session_id:
            return {"error": "No active session", "status": "rejected"}
        if tokens_used is None or tokens_used <= 0:
            return {"error": "Invalid token amount", "status": "rejected"}
        if not self.rate_limiter.allow_request():
            handle_error("Rate limit exceeded", context="voice_add_tokens")
            return {"error": "Rate limit exceeded", "status": "throttled", "retry_after": 60}
        self.token_count += tokens_used
        self.turn_count += 1
        if self.token_count > self.max_tokens and self.user_tier in ["SUPERGROK", "HEAVY"]:
            old_limit = self.max_tokens
            self.max_tokens += self.extend_by
            persist_brain(self.brain_state["state"], new_logs=[{"type": "voice_token_extended", "session_id": self.session_id, "old_limit": old_limit, "new_limit": self.max_tokens}])
        return {"turns": self.turn_count, "tokens_used": self.token_count, "max_tokens": self.max_tokens, "status": "ok"}

    async def _auto_audit_heartbeat(self):
        while True:
            await asyncio.sleep(30 * 60)
            if self.session_id:
                try:
                    self.last_rotation = time.time()
                    persist_brain(self.brain_state["state"], new_logs=[{"type": "voice_token_rotation", "session_id": self.session_id, "timestamp": self.last_rotation}])
                    print(f"🔄 Audit heartbeat logged (chat preserved)")
                except Exception as e:
                    handle_error(e, context="voice_auto_rotation")

    def stop(self):
        if self._rotation_task and not self._rotation_task.done():
            self._rotation_task.cancel()
        if self.session_id:
            persist_brain(self.brain_state["state"], new_logs=[{"type": "voice_session_stop", "session_id": self.session_id, "final_tokens": self.token_count, "turns": self.turn_count}])

    def sanitize_old_tokens(self):
        try:
            self.memory_manager.sanitize_expired_tokens(self.session_id)
        except Exception as e:
            handle_error(e, context="voice_sanitize")

    def get_status(self) -> dict:
        return {"active": True, "tier": self.user_tier, "turns": self.turn_count, "tokens_used": self.token_count, "max_tokens": self.max_tokens, "last_rotation": self.last_rotation}