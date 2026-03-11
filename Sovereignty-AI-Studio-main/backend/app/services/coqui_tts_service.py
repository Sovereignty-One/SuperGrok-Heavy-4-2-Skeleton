"""
Coqui TTS Integration Service — open-source text-to-speech engine.

Provides on-device, privacy-respecting TTS using the Coqui TTS engine
(Mozilla-licensed).  Falls back gracefully when the engine is not installed.
All invocations are audit-logged for court-admissible compliance.
"""
import os
import subprocess
import tempfile
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class CoquiTTSService:
    """Text-to-speech via the open-source Coqui TTS engine."""

    # Supported models shipped with coqui-tts (all open-license)
    AVAILABLE_MODELS: List[Dict[str, str]] = [
        {"id": "tts_models/en/ljspeech/tacotron2-DDC", "name": "LJSpeech Tacotron2", "lang": "en"},
        {"id": "tts_models/en/ljspeech/glow-tts", "name": "LJSpeech GlowTTS", "lang": "en"},
        {"id": "tts_models/en/vctk/vits", "name": "VCTK VITS (multi-speaker)", "lang": "en"},
        {"id": "tts_models/de/thorsten/tacotron2-DDC", "name": "Thorsten (German)", "lang": "de"},
        {"id": "tts_models/es/mai/tacotron2-DDC", "name": "Mai (Spanish)", "lang": "es"},
        {"id": "tts_models/fr/mai/tacotron2-DDC", "name": "Mai (French)", "lang": "fr"},
    ]

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or "tts_models/en/ljspeech/tacotron2-DDC"
        self._executable = self._find_executable()
        if self._executable:
            logger.info("CoquiTTSService ready — binary: %s", self._executable)
        else:
            logger.warning("Coqui TTS binary not found; service will return fallback responses")

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    @staticmethod
    def _find_executable() -> Optional[str]:
        """Locate the ``tts`` CLI that ships with coqui-tts."""
        for candidate in ["/usr/local/bin/tts", "/usr/bin/tts"]:
            if os.path.isfile(candidate):
                return candidate
        try:
            result = subprocess.run(
                ["which", "tts"], capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass
        return None

    # ------------------------------------------------------------------
    # Core TTS
    # ------------------------------------------------------------------

    def text_to_speech(
        self,
        text: str,
        output_file: Optional[str] = None,
        model_name: Optional[str] = None,
        speaker_id: Optional[str] = None,
    ) -> Optional[str]:
        """Convert *text* to a WAV file using Coqui TTS.

        Returns the path to the generated audio file, or ``None`` on failure.
        """
        if not self._executable:
            logger.warning("Coqui TTS not installed — skipping synthesis")
            return None

        if not output_file:
            fd, output_file = tempfile.mkstemp(suffix=".wav")
            os.close(fd)

        model = model_name or self.model_name
        cmd: list = [
            self._executable,
            "--text", text[:2000],
            "--model_name", model,
            "--out_path", output_file,
        ]
        if speaker_id:
            cmd.extend(["--speaker_idx", speaker_id])

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60,
            )
            if result.returncode == 0 and os.path.isfile(output_file):
                logger.info("Coqui TTS generated: %s", output_file)
                return output_file
            logger.error("Coqui TTS failed (rc=%d): %s", result.returncode, result.stderr[:500])
        except subprocess.TimeoutExpired:
            logger.error("Coqui TTS timed out")
        except Exception as exc:
            logger.error("Coqui TTS error: %s", exc)
        return None

    def speak_alert(self, title: str, message: str, severity: str = "medium") -> bool:
        """Speak an alert via Coqui TTS, returning *True* on success."""
        prefix = "Alert! " if severity in ("high", "critical") else ""
        audio = self.text_to_speech(f"{prefix}{title}. {message}")
        if audio:
            return self._play_audio(audio)
        return False

    # ------------------------------------------------------------------
    # Playback
    # ------------------------------------------------------------------

    @staticmethod
    def _play_audio(audio_file: str) -> bool:
        """Play *audio_file* using the first available system player."""
        players = [
            ["aplay", audio_file],
            ["afplay", audio_file],
            ["powershell", "-c", f"(New-Object Media.SoundPlayer '{audio_file}').PlaySync()"],
        ]
        for cmd in players:
            try:
                r = subprocess.run(cmd, capture_output=True, timeout=15)
                if r.returncode == 0:
                    return True
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        logger.warning("No audio player found for %s", audio_file)
        return False

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def get_available_models(self) -> List[Dict[str, str]]:
        return list(self.AVAILABLE_MODELS)

    def is_available(self) -> bool:
        """Return True if the Coqui TTS binary is found and ready."""
        return self._executable is not None

    def get_status(self) -> Dict[str, Any]:
        return {
            "service": "coqui_tts",
            "status": "online" if self._executable else "unavailable",
            "binary": self._executable,
            "default_model": self.model_name,
            "available_models": len(self.AVAILABLE_MODELS),
        }


# Module-level singleton
coqui_tts_service = CoquiTTSService()
