"""
Coqui TTS Service — Real neural voice synthesis for SuperGrok.

Uses the Coqui TTS library (coqui-ai/TTS) for high-quality,
multi-speaker, multilingual text-to-speech. Supports:
  - XTTS v2 (multilingual, voice cloning)
  - Tacotron2-DDC (fast English)
  - VITS (fast multilingual)

Can run as a standalone HTTP server or be imported as a library.

Usage:
  # As HTTP server (port 5002):
  python coqui_tts_service.py --serve

  # As library:
  from coqui_tts_service import CoquiTTSService
  svc = CoquiTTSService()
  svc.text_to_speech("Hello world", "/tmp/out.wav")
"""
import os
import sys
import json
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Available Coqui models (name → model_name for TTS library)
COQUI_MODELS = {
    "en-default":  "tts_models/en/ljspeech/tacotron2-DDC",
    "en-vctk":     "tts_models/en/vctk/vits",
    "en-jenny":    "tts_models/en/jenny/jenny",
    "multi-xtts":  "tts_models/multilingual/multi-dataset/xtts_v2",
    "de-thorsten": "tts_models/de/thorsten/tacotron2-DDC",
    "es-css10":    "tts_models/es/css10/vits",
    "fr-css10":    "tts_models/fr/css10/vits",
    "ja-kokoro":   "tts_models/ja/kokoro/tacotron2-DDC",
}


class CoquiTTSService:
    """Coqui TTS service with model management and audio generation."""

    def __init__(self, model_name: str = "en-default"):
        """
        Initialize Coqui TTS service.

        Args:
            model_name: Key from COQUI_MODELS or a full tts_models/... path.
        """
        self.model_name = COQUI_MODELS.get(model_name, model_name)
        self._tts = None
        self._available = self._check_available()

    @property
    def is_available(self) -> bool:
        return self._available

    def _check_available(self) -> bool:
        """Check if the TTS library is installed."""
        try:
            import TTS  # noqa: F401
            return True
        except ImportError:
            logger.warning(
                "Coqui TTS not installed. Install with: pip install TTS"
            )
            return False

    def _get_tts(self):
        """Lazy-load the TTS model."""
        if self._tts is None:
            try:
                from TTS.api import TTS as CoquiTTS
                self._tts = CoquiTTS(model_name=self.model_name, progress_bar=False)
                logger.info("Coqui TTS model loaded: %s", self.model_name)
            except Exception as e:
                logger.error("Failed to load Coqui model %s: %s", self.model_name, e)
                self._available = False
        return self._tts

    def text_to_speech(
        self,
        text: str,
        output_file: Optional[str] = None,
        speaker: Optional[str] = None,
        language: Optional[str] = None,
        speed: float = 1.0,
    ) -> Optional[str]:
        """
        Convert text to speech using Coqui TTS.

        Args:
            text: Text to synthesize.
            output_file: Output WAV path (auto-generated if None).
            speaker: Speaker ID for multi-speaker models.
            language: Language code for multilingual models.
            speed: Playback speed multiplier.

        Returns:
            Path to generated WAV file, or None on failure.
        """
        if not self._available:
            logger.warning("Coqui TTS not available, skipping")
            return None

        if not output_file:
            fd, output_file = tempfile.mkstemp(suffix=".wav")
            os.close(fd)

        tts = self._get_tts()
        if tts is None:
            return None

        try:
            kwargs = {}
            if speaker:
                kwargs["speaker"] = speaker
            if language:
                kwargs["language"] = language
            if speed != 1.0:
                kwargs["speed"] = speed

            tts.tts_to_file(text=text, file_path=output_file, **kwargs)

            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                logger.info("Generated Coqui TTS audio: %s", output_file)
                return output_file
            else:
                logger.error("Coqui TTS produced empty output")
                return None
        except Exception as e:
            logger.error("Coqui TTS error: %s", e)
            return None

    def list_models(self) -> list:
        """List available Coqui TTS models."""
        return list(COQUI_MODELS.items())

    def speak_alert(
        self,
        title: str,
        message: str,
        severity: str = "medium",
    ) -> bool:
        """Speak an alert using Coqui TTS with system audio playback."""
        if severity in ("high", "critical"):
            text = f"Alert! {title}. {message}"
        else:
            text = f"{title}. {message}"

        audio_file = self.text_to_speech(text)
        if not audio_file:
            return False

        return self._play_audio(audio_file)

    def _play_audio(self, audio_file: str) -> bool:
        """Play audio using available system player."""
        players = [
            ["aplay", audio_file],
            ["afplay", audio_file],
            ["powershell", "-c",
             f"(New-Object Media.SoundPlayer '{audio_file}').PlaySync()"],
        ]
        for cmd in players:
            try:
                result = subprocess.run(cmd, capture_output=True, timeout=30)
                if result.returncode == 0:
                    return True
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        logger.warning("No audio player found for playback")
        return False


def run_server(host: str = "127.0.0.1", port: int = 5002, model: str = "en-default"):
    """Run Coqui TTS as an HTTP server compatible with the Unified Server bridge."""
    try:
        from TTS.server.server import create_app
        app = create_app(model_name=COQUI_MODELS.get(model, model))
        logger.info("Starting Coqui TTS server on %s:%d with model %s", host, port, model)
        app.run(host=host, port=port)
    except ImportError:
        # Fallback: use tts-server CLI
        model_path = COQUI_MODELS.get(model, model)
        cmd = [sys.executable, "-m", "TTS.server.server",
               "--model_name", model_path, "--port", str(port)]
        logger.info("Starting Coqui TTS server: %s", " ".join(cmd))
        subprocess.run(cmd)


# Global instance (lazy — only loads model when first used)
coqui_service = CoquiTTSService()


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [COQUI] %(message)s")

    parser = argparse.ArgumentParser(description="Coqui TTS Service")
    parser.add_argument("--serve", action="store_true", help="Run as HTTP server")
    parser.add_argument("--port", type=int, default=5002, help="Server port")
    parser.add_argument("--model", default="en-default", help="Model name")
    parser.add_argument("--text", help="Text to speak (one-shot mode)")
    parser.add_argument("--output", help="Output WAV file path")
    args = parser.parse_args()

    if args.serve:
        run_server(port=args.port, model=args.model)
    elif args.text:
        svc = CoquiTTSService(model_name=args.model)
        out = svc.text_to_speech(args.text, output_file=args.output)
        if out:
            print(f"Audio saved to: {out}")
        else:
            print("TTS failed", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
