import time
import asyncio
import secrets
from fixers.persist_brain import persist_brain, hydrate_brain
from fixers.handle_error import handle_error
from fixers.rate_limiter import RateLimiter
from fixers.memory_manager import MemoryManager

class SuperGrokVoiceHandler:
    def __init__(self, brain_state: dict = None, user_tier: str = "SUPERGROK"):
        self.brain_state = brain_state or {"state": {}, "scarlog": []}
        
        # === REPMHL: Hydrate brain on init (preserves memory across key rotations) ===
        if "state" not in self.brain_state or not self.brain_state["state"]:
            self.brain_state = hydrate_brain() or self.brain_state

        self.user_tier = user_tier.upper()
        self.session_id = None
        self.token_count = 0
        self.turn_count = 0
        self.last_rotation = time.time()
        self.key_rotation_count = 0

        # More generous limits
        if self.user_tier == "SUPERGROK":
            self.base_limit = 32768
            self.extend_by = 16384
        elif self.user_tier == "HEAVY":
            self.base_limit = 131072
            self.extend_by = 65536
        else:
            self.base_limit = 8192
            self.extend_by = 4096

        self.max_tokens = self.base_limit
        self.rate_limiter = RateLimiter(max_requests=120, window_seconds=60)
        self.memory_manager = MemoryManager(self.brain_state, max_logs=500)

        self._rotation_task = asyncio.create_task(self._auto_audit_heartbeat())

    async def start_session(self) -> dict:
        if self.session_id:
            return {"status": "already_active", "session_id": self.session_id}

        self.session_id = f"voice-{secrets.token_hex(8)}-{self.user_tier}"
        self.token_count = 0
        self.turn_count = 0

        persist_brain(self.brain_state["state"], new_logs=[{
            "type": "voice_session_start",
            "session_id": self.session_id,
            "tier": self.user_tier,
            "base_limit": self.base_limit,
            "repmhl_preserved": True
        }])

        return {
            "status": "active",
            "session_id": self.session_id,
            "max_tokens": self.max_tokens,
            "message": f"SuperGrok voice ready • {self.max_tokens} tokens (REPMHL active)"
        }

    async def add_tokens(self, tokens_used: int) -> dict:
        if not self.session_id:
            return {"error": "No active session", "status": "rejected"}

        if tokens_used is None or tokens_used <= 0:
            return {"error": "Invalid token amount", "status": "rejected"}

        if not self.rate_limiter.allow_request():
            handle_error("Rate limit exceeded", context="voice_add_tokens")
            return {"error": "Rate limit exceeded", "status": "throttled", "retry_after": 30}

        self.token_count += tokens_used
        self.turn_count += 1

        # More aggressive extension for paid tiers
        if self.token_count > self.max_tokens and self.user_tier in ["SUPERGROK", "HEAVY"]:
            old_limit = self.max_tokens
            self.max_tokens += self.extend_by
            persist_brain(self.brain_state["state"], new_logs=[{
                "type": "voice_token_extended",
                "session_id": self.session_id,
                "old_limit": old_limit,
                "new_limit": self.max_tokens,
                "repmhl_preserved": True
            }])

        return {
            "turns": self.turn_count,
            "tokens_used": self.token_count,
            "max_tokens": self.max_tokens,
            "status": "ok"
        }

    async def _auto_audit_heartbeat(self):
        while True:
            await asyncio.sleep(30 * 60)
            if self.session_id:
                try:
                    self.last_rotation = time.time()
                    persist_brain(self.brain_state["state"], new_logs=[{
                        "type": "voice_token_rotation",
                        "session_id": self.session_id,
                        "timestamp": self.last_rotation,
                        "repmhl_preserved": True
                    }])
                    print(f"🔄 Audit heartbeat + REPMHL preserved")
                except Exception as e:
                    handle_error(e, context="voice_auto_rotation")

    def stop(self):
        if hasattr(self, '_rotation_task') and not self._rotation_task.done():
            self._rotation_task.cancel()

        if self.session_id:
            persist_brain(self.brain_state["state"], new_logs=[{
                "type": "voice_session_stop",
                "session_id": self.session_id,
                "final_tokens": self.token_count,
                "turns": self.turn_count,
                "repmhl_preserved": True
            }])

    # === NEW: Key rotation with full REPMHL preservation ===
    def rotate_key(self):
        """Called when master key rotates — preserves full memory hydration."""
        self.key_rotation_count += 1
        old_state = self.brain_state.copy()

        # Re-hydrate from persistent storage
        new_state = hydrate_brain() or {"state": {}, "scarlog": []}
        self.brain_state = new_state

        persist_brain(self.brain_state["state"], new_logs=[{
            "type": "key_rotation_with_repmhl",
            "old_key_rotation": self.key_rotation_count - 1,
            "new_key_rotation": self.key_rotation_count,
            "memory_preserved": True,
            "timestamp": time.time()
        }])

        print(f"🔑 Key rotated + REPMHL fully hydrated (rotation #{self.key_rotation_count})")
        return self.brain_state