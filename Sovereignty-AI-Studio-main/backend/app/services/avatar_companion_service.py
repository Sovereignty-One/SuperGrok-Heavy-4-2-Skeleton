"""
Avatar Companion Service – on-device AI avatar for interactive user guidance.

Provides a persistent AI avatar companion with configurable personality,
appearance, and interaction modes for the Sovereignty AI Studio.
Supports 3-D CGI rendering with fully designable human-looking avatars.
"""
import uuid
import logging
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class AvatarMood(str, Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    THINKING = "thinking"
    ALERT = "alert"
    FOCUSED = "focused"


class AvatarStyle(str, Enum):
    MINIMAL = "minimal"
    REALISTIC = "realistic"
    ANIME = "anime"
    ROBOTIC = "robotic"
    CGI_HUMAN = "cgi_human"
    HOLOGRAPHIC = "holographic"


@dataclass
class CGIAppearance:
    """3-D CGI appearance configuration for the avatar."""
    skin_tone: str = "#C68642"
    hair_color: str = "#2C1B0E"
    hair_style: str = "short_wavy"
    eye_color: str = "#4A90D9"
    clothing_style: str = "smart_casual"
    face_shape: str = "oval"
    height_cm: int = 170
    render_quality: str = "high"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skin_tone": self.skin_tone,
            "hair_color": self.hair_color,
            "hair_style": self.hair_style,
            "eye_color": self.eye_color,
            "clothing_style": self.clothing_style,
            "face_shape": self.face_shape,
            "height_cm": self.height_cm,
            "render_quality": self.render_quality,
        }


@dataclass
class AvatarProfile:
    """Avatar companion configuration."""
    avatar_id: str
    user_id: str
    name: str = "Ara"
    style: AvatarStyle = AvatarStyle.MINIMAL
    mood: AvatarMood = AvatarMood.NEUTRAL
    voice_id: str = "en_US-lessac-medium"
    personality: str = "helpful"
    created_at: str = ""
    interaction_count: int = 0
    preferences: Dict[str, Any] = field(default_factory=dict)
    cgi_appearance: CGIAppearance = field(default_factory=CGIAppearance)
    opar_linked: bool = False

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


class AvatarCompanionService:
    """Manages AI avatar companions for users."""

    def __init__(self):
        self._avatars: Dict[str, AvatarProfile] = {}
        logger.info("AvatarCompanionService initialised")

    def create_avatar(
        self,
        user_id: str,
        name: str = "Ara",
        style: str = "minimal",
        voice_id: str = "en_US-lessac-medium",
        personality: str = "helpful",
        cgi_overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new avatar companion for a user."""
        cgi = CGIAppearance()
        if cgi_overrides:
            for key, val in cgi_overrides.items():
                if hasattr(cgi, key):
                    setattr(cgi, key, val)
        avatar = AvatarProfile(
            avatar_id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            style=AvatarStyle(style),
            voice_id=voice_id,
            personality=personality,
            cgi_appearance=cgi,
        )
        self._avatars[avatar.avatar_id] = avatar
        logger.info("Avatar '%s' (%s) created for user %s", name, avatar.avatar_id, user_id)
        return self._avatar_to_dict(avatar)

    def get_avatar(self, avatar_id: str) -> Optional[Dict[str, Any]]:
        avatar = self._avatars.get(avatar_id)
        return self._avatar_to_dict(avatar) if avatar else None

    def get_user_avatar(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get the primary avatar for a user."""
        for avatar in self._avatars.values():
            if avatar.user_id == user_id:
                return self._avatar_to_dict(avatar)
        return None

    def update_mood(self, avatar_id: str, mood: str) -> Optional[Dict[str, Any]]:
        avatar = self._avatars.get(avatar_id)
        if not avatar:
            return None
        avatar.mood = AvatarMood(mood)
        return self._avatar_to_dict(avatar)

    def interact(self, avatar_id: str, message: str) -> Dict[str, Any]:
        """Handle an interaction with the avatar companion."""
        avatar = self._avatars.get(avatar_id)
        if not avatar:
            return {"error": "Avatar not found"}

        avatar.interaction_count += 1
        avatar.mood = AvatarMood.THINKING

        response = self._generate_avatar_response(avatar, message)
        avatar.mood = AvatarMood.HAPPY

        return {
            "avatar_id": avatar.avatar_id,
            "name": avatar.name,
            "mood": avatar.mood.value,
            "response": response,
            "interaction_count": avatar.interaction_count,
        }

    def delete_avatar(self, avatar_id: str) -> bool:
        if avatar_id in self._avatars:
            del self._avatars[avatar_id]
            return True
        return False

    def get_status(self) -> Dict[str, Any]:
        return {
            "service": "avatar_companion",
            "status": "online",
            "active_avatars": len(self._avatars),
            "available_styles": [s.value for s in AvatarStyle],
            "available_moods": [m.value for m in AvatarMood],
            "cgi_3d_enabled": True,
            "opar_linkable": True,
        }

    # ── 3-D CGI appearance ───────────────────────────────────────────

    def update_cgi_appearance(
        self, avatar_id: str, updates: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Update the 3-D CGI appearance of an avatar."""
        avatar = self._avatars.get(avatar_id)
        if not avatar:
            return None
        cgi = avatar.cgi_appearance
        for key, val in updates.items():
            if hasattr(cgi, key):
                setattr(cgi, key, val)
        logger.info("Avatar %s CGI appearance updated", avatar_id)
        return self._avatar_to_dict(avatar)

    def link_opar(self, avatar_id: str, linked: bool = True) -> Optional[Dict[str, Any]]:
        """Link or unlink an avatar to the OPAR system."""
        avatar = self._avatars.get(avatar_id)
        if not avatar:
            return None
        avatar.opar_linked = linked
        return self._avatar_to_dict(avatar)

    # ── Private helpers ──────────────────────────────────────────────

    def _generate_avatar_response(
        self, avatar: AvatarProfile, message: str
    ) -> str:
        """Generate a contextual response from the avatar."""
        greeting_words = {"hello", "hi", "hey"}
        if message.lower().strip() in greeting_words:
            return f"Hi there! I'm {avatar.name}, your AI companion. How can I assist you?"
        if "help" in message.lower():
            return (
                f"Of course! As {avatar.name}, I can guide you through "
                "media creation, project building, voice interaction, and more."
            )
        return f"Got it! Let me work on that for you."

    @staticmethod
    def _avatar_to_dict(avatar: AvatarProfile) -> Dict[str, Any]:
        return {
            "avatar_id": avatar.avatar_id,
            "user_id": avatar.user_id,
            "name": avatar.name,
            "style": avatar.style.value,
            "mood": avatar.mood.value,
            "voice_id": avatar.voice_id,
            "personality": avatar.personality,
            "created_at": avatar.created_at,
            "interaction_count": avatar.interaction_count,
            "cgi_appearance": avatar.cgi_appearance.to_dict(),
            "opar_linked": avatar.opar_linked,
        }


# Module-level singleton
avatar_companion_service = AvatarCompanionService()
