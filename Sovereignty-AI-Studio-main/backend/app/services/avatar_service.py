"""
Avatar Companion Service
Manages AI avatar state, expressions, and interaction.
Integrates with Piper TTS for voice output and EEG for emotional feedback.
"""
import logging
from typing import Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class AvatarMood(str, Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    FOCUSED = "focused"
    ALERT = "alert"
    CALM = "calm"


class AvatarService:
    """Service managing the AI avatar companion state and interactions."""

    def __init__(self):
        self._state = {
            "name": "Ara",
            "mood": AvatarMood.NEUTRAL,
            "expression": "default",
            "last_interaction": None,
            "context": {},
            "voice_enabled": True,
            "eeg_linked": False,
        }

    def get_state(self) -> Dict[str, Any]:
        """Get current avatar state."""
        return {
            "name": self._state["name"],
            "mood": self._state["mood"].value,
            "expression": self._state["expression"],
            "voice_enabled": self._state["voice_enabled"],
            "eeg_linked": self._state["eeg_linked"],
        }

    def update_mood(self, mood: str) -> Dict[str, Any]:
        """Update avatar mood based on interaction or EEG data."""
        try:
            self._state["mood"] = AvatarMood(mood)
        except ValueError:
            self._state["mood"] = AvatarMood.NEUTRAL
            logger.warning(f"Unknown mood '{mood}', defaulting to neutral")

        expression_map = {
            AvatarMood.NEUTRAL: "default",
            AvatarMood.HAPPY: "smile",
            AvatarMood.FOCUSED: "concentrate",
            AvatarMood.ALERT: "wide_eyes",
            AvatarMood.CALM: "serene",
        }
        self._state["expression"] = expression_map.get(
            self._state["mood"], "default"
        )
        return self.get_state()

    def interact(self, message: str) -> Dict[str, Any]:
        """Process user interaction and update avatar state."""
        self._state["last_interaction"] = message
        return {
            "avatar": self.get_state(),
            "response": f"Ara acknowledges: {message}",
            "action": "respond",
        }

    def link_eeg(self, enabled: bool = True) -> Dict[str, Any]:
        """Link or unlink EEG data feed to avatar mood."""
        self._state["eeg_linked"] = enabled
        return {
            "eeg_linked": enabled,
            "message": f"EEG link {'enabled' if enabled else 'disabled'}",
        }


# Global instance
avatar_service = AvatarService()
