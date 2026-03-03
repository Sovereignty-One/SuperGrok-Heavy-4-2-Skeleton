"""
Music Generation Service
Provides music composition and generation capabilities.
Uses on-device synthesis for sovereign operation.
"""
import logging
from typing import Optional, Dict, Any, List
from enum import Enum

logger = logging.getLogger(__name__)


class MusicGenre(str, Enum):
    AMBIENT = "ambient"
    ELECTRONIC = "electronic"
    CLASSICAL = "classical"
    LO_FI = "lo-fi"
    CINEMATIC = "cinematic"
    FOCUS = "focus"


class MusicService:
    """Service for music generation and composition."""

    def __init__(self):
        self._compositions = []
        self._next_id = 1

    def get_genres(self) -> List[Dict[str, str]]:
        """Get all supported music genres."""
        return [
            {"id": g.value, "name": g.value.replace("-", " ").title()}
            for g in MusicGenre
        ]

    def create_composition(
        self,
        prompt: str,
        genre: str = "ambient",
        duration_seconds: int = 60,
        bpm: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create a music composition request.

        Args:
            prompt: Text description of desired music
            genre: Music genre
            duration_seconds: Target duration
            bpm: Beats per minute (optional)
        """
        composition = {
            "id": self._next_id,
            "prompt": prompt,
            "genre": genre,
            "duration_seconds": duration_seconds,
            "bpm": bpm or self._default_bpm(genre),
            "status": "pending",
            "audio_file": None,
        }
        self._compositions.append(composition)
        self._next_id += 1
        logger.info(f"Music composition created: {composition['id']}")
        return composition

    def get_composition(self, composition_id: int) -> Optional[Dict[str, Any]]:
        """Get a composition by ID."""
        for c in self._compositions:
            if c["id"] == composition_id:
                return c
        return None

    def list_compositions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List all compositions."""
        return self._compositions[-limit:]

    def _default_bpm(self, genre: str) -> int:
        """Get default BPM for a genre."""
        bpm_map = {
            "ambient": 70,
            "electronic": 128,
            "classical": 100,
            "lo-fi": 85,
            "cinematic": 90,
            "focus": 60,
        }
        return bpm_map.get(genre, 100)


# Global instance
music_service = MusicService()
