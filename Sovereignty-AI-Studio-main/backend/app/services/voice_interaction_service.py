"""
Voice Interaction Service – AI-to-User bidirectional voice exchange via Piper TTS.

Provides conversational voice interaction between the AI assistant and the user,
supporting text-to-speech output, voice command routing, and session management.
"""
import os
import uuid
import logging
import tempfile
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class VoiceState(str, Enum):
    """Voice interaction session states."""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"


@dataclass
class VoiceSession:
    """Represents an active voice interaction session."""
    session_id: str
    user_id: str
    state: VoiceState = VoiceState.IDLE
    created_at: str = ""
    last_activity: str = ""
    history: List[Dict[str, str]] = field(default_factory=list)
    voice_model: str = "en_US-lessac-medium"
    sample_rate: int = 22050

    def __post_init__(self):
        now = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.last_activity:
            self.last_activity = now


class VoiceInteractionService:
    """Bidirectional voice interaction service using Piper TTS."""

    def __init__(
        self,
        piper_dir: Optional[str] = None,
        model_path: Optional[str] = None,
        output_dir: Optional[str] = None,
    ):
        self.piper_dir = piper_dir or os.path.join(
            Path(__file__).parent.parent.parent.parent, "piper-tts"
        )
        self.model_path = model_path
        self.output_dir = output_dir or tempfile.gettempdir()
        self._sessions: Dict[str, VoiceSession] = {}
        logger.info("VoiceInteractionService initialised")

    # ── Session management ───────────────────────────────────────────

    def create_session(
        self, user_id: str, voice_model: str = "en_US-lessac-medium"
    ) -> VoiceSession:
        """Create a new voice interaction session."""
        session = VoiceSession(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            voice_model=voice_model,
        )
        self._sessions[session.session_id] = session
        logger.info("Voice session %s created for user %s", session.session_id, user_id)
        return session

    def get_session(self, session_id: str) -> Optional[VoiceSession]:
        return self._sessions.get(session_id)

    def end_session(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info("Voice session %s ended", session_id)
            return True
        return False

    def list_sessions(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        sessions = self._sessions.values()
        if user_id:
            sessions = [s for s in sessions if s.user_id == user_id]
        return [
            {
                "session_id": s.session_id,
                "user_id": s.user_id,
                "state": s.state.value,
                "created_at": s.created_at,
                "last_activity": s.last_activity,
                "message_count": len(s.history),
            }
            for s in sessions
        ]

    # ── Voice interaction ────────────────────────────────────────────

    def process_text_input(
        self, session_id: str, text: str
    ) -> Dict[str, Any]:
        """Process user text input and generate AI voice response."""
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found", "session_id": session_id}

        session.state = VoiceState.PROCESSING
        session.last_activity = datetime.now(timezone.utc).isoformat()

        # Record user message
        session.history.append({"role": "user", "content": text})

        # Generate AI response (stubbed – production connects to LLM)
        ai_response = self._generate_response(text, session.history)
        session.history.append({"role": "assistant", "content": ai_response})

        # Generate voice output path
        audio_path = os.path.join(
            self.output_dir,
            f"voice_{session.session_id}_{len(session.history)}.wav",
        )

        session.state = VoiceState.SPEAKING
        return {
            "session_id": session.session_id,
            "response_text": ai_response,
            "audio_path": audio_path,
            "state": session.state.value,
            "message_count": len(session.history),
        }

    def _generate_response(
        self, user_text: str, history: List[Dict[str, str]]
    ) -> str:
        """Generate an AI response to user input.

        In production this delegates to the configured LLM backend.
        """
        greetings = {"hello", "hi", "hey", "greetings"}
        if user_text.lower().strip() in greetings:
            return "Hello! I'm your AI assistant. How can I help you today?"
        if "help" in user_text.lower():
            return (
                "I can help with media generation, project management, "
                "voice interaction, and more. What would you like to do?"
            )
        return f"I received your message: '{user_text}'. Processing your request."

    # ── Configuration ────────────────────────────────────────────────

    def get_available_voices(self) -> List[Dict[str, str]]:
        """Return list of available Piper voice models."""
        return [
            {"id": "en_US-lessac-medium", "name": "Lessac (US English)", "lang": "en-US"},
            {"id": "en_US-amy-medium", "name": "Amy (US English)", "lang": "en-US"},
            {"id": "en_GB-alba-medium", "name": "Alba (British English)", "lang": "en-GB"},
            {"id": "de_DE-thorsten-medium", "name": "Thorsten (German)", "lang": "de-DE"},
            {"id": "es_ES-mls_9972-medium", "name": "MLS (Spanish)", "lang": "es-ES"},
        ]

    def get_status(self) -> Dict[str, Any]:
        """Return service status."""
        return {
            "service": "voice_interaction",
            "status": "online",
            "active_sessions": len(self._sessions),
            "tts_engine": "piper",
            "available_voices": len(self.get_available_voices()),
        }


# Module-level singleton
voice_interaction_service = VoiceInteractionService()
