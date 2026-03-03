"""
Piper TTS Integration for Alert Audio Notifications
Provides text-to-speech capabilities for live alerts
"""
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class PiperTTSService:
    """Service for converting alert text to speech using Piper"""
    
    def __init__(self, piper_dir: Optional[str] = None, model_path: Optional[str] = None):
        """
        Initialize Piper TTS service
        
        Args:
            piper_dir: Path to piper installation directory
            model_path: Path to piper voice model (.onnx file)
        """
        self.piper_dir = piper_dir or os.path.join(
            Path(__file__).parent.parent.parent.parent,
            "piper-tts"
        )
        self.model_path = model_path
        self.piper_executable = self._find_piper_executable()
        
    def _find_piper_executable(self) -> Optional[str]:
        """Find the piper executable"""
        # Check common locations
        possible_paths = [
            os.path.join(self.piper_dir, "piper"),
            os.path.join(self.piper_dir, "build", "piper"),
            "/usr/local/bin/piper",
            "/usr/bin/piper",
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
                
        # Try to find in PATH
        try:
            result = subprocess.run(
                ["which", "piper"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
            
        logger.warning("Piper executable not found. Audio alerts will be disabled.")
        return None
    
    def text_to_speech(self, text: str, output_file: Optional[str] = None) -> Optional[str]:
        """
        Convert text to speech
        
        Args:
            text: Text to convert
            output_file: Output file path (optional, creates temp file if not provided)
            
        Returns:
            Path to the generated audio file, or None if failed
        """
        if not self.piper_executable:
            logger.warning("Piper not available, skipping TTS")
            return None
            
        if not self.model_path or not os.path.exists(self.model_path):
            logger.warning("Piper model not found, skipping TTS")
            return None
        
        # Create output file if not provided
        if not output_file:
            fd, output_file = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
        
        try:
            # Run piper TTS
            cmd = [
                self.piper_executable,
                "--model", self.model_path,
                "--output_file", output_file
            ]
            
            result = subprocess.run(
                cmd,
                input=text,
                text=True,
                capture_output=True,
                timeout=30
            )
            
            if result.returncode == 0 and os.path.exists(output_file):
                logger.info(f"Generated TTS audio: {output_file}")
                return output_file
            else:
                logger.error(f"Piper TTS failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Error running Piper TTS: {e}")
            return None
    
    def speak_alert(self, alert_title: str, alert_message: str, severity: str = "medium") -> bool:
        """
        Speak an alert using TTS
        
        Args:
            alert_title: Alert title
            alert_message: Alert message
            severity: Alert severity (low, medium, high, critical)
            
        Returns:
            True if successful, False otherwise
        """
        # Build spoken text based on severity
        if severity in ["high", "critical"]:
            spoken_text = f"Alert! {alert_title}. {alert_message}"
        else:
            spoken_text = f"{alert_title}. {alert_message}"
        
        audio_file = self.text_to_speech(spoken_text)
        
        if audio_file:
            # Play the audio file
            return self._play_audio(audio_file)
        
        return False
    
    def _play_audio(self, audio_file: str) -> bool:
        """
        Play an audio file
        
        Args:
            audio_file: Path to audio file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Try different audio players
            players = [
                ["aplay", audio_file],  # Linux
                ["afplay", audio_file],  # macOS
                ["powershell", "-c", f"(New-Object Media.SoundPlayer '{audio_file}').PlaySync()"],  # Windows
            ]
            
            for player_cmd in players:
                try:
                    result = subprocess.run(
                        player_cmd,
                        capture_output=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        logger.info(f"Played audio file: {audio_file}")
                        return True
                except FileNotFoundError:
                    continue
                except Exception as e:
                    logger.warning(f"Failed to play with {player_cmd[0]}: {e}")
                    continue
            
            logger.warning("No audio player found")
            return False
            
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
            return False
        finally:
            # Clean up temp file
            try:
                if os.path.exists(audio_file):
                    os.unlink(audio_file)
            except Exception:
                pass


# Global instance
piper_service = PiperTTSService()
