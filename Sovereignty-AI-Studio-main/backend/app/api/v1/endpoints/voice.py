"""
Voice interaction API endpoints.
Provides voice chat and TTS capabilities using Piper TTS.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class VoiceRequest(BaseModel):
    text: str
    voice_model: Optional[str] = None
    speed: float = 1.0


class VoiceResponse(BaseModel):
    status: str
    message: str
    audio_file: Optional[str] = None
    voice_model: str = "piper-default"


@router.post("/speak", response_model=VoiceResponse)
async def text_to_speech(request: VoiceRequest):
    """
    Convert text to speech using Piper TTS.

    Returns the path to the generated audio file.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        from app.services.piper_tts_service import piper_service
        audio_file = piper_service.text_to_speech(request.text)
        if audio_file:
            return VoiceResponse(
                status="completed",
                message="Audio generated successfully",
                audio_file=audio_file,
                voice_model=request.voice_model or "piper-default",
            )
        return VoiceResponse(
            status="unavailable",
            message="Piper TTS not available. Install piper and configure PIPER_MODEL_PATH.",
        )
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return VoiceResponse(
            status="error",
            message=f"TTS generation failed: {str(e)}",
        )


@router.post("/chat", response_model=dict)
async def voice_chat(request: VoiceRequest):
    """
    Voice interaction endpoint.
    Processes text input and returns AI response with optional TTS.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    # Generate AI response (placeholder - integrates with sovereign mind)
    ai_response = f"Acknowledged: {request.text}"

    result = {
        "input": request.text,
        "response": ai_response,
        "audio_file": None,
        "status": "completed",
    }

    # Generate audio for response
    try:
        from app.services.piper_tts_service import piper_service
        audio_file = piper_service.text_to_speech(ai_response)
        if audio_file:
            result["audio_file"] = audio_file
    except Exception as e:
        logger.warning(f"Voice chat TTS failed: {e}")

    return result


@router.get("/status", response_model=dict)
async def voice_status():
    """Check voice system status and available models."""
    try:
        from app.services.piper_tts_service import piper_service
        piper_available = piper_service.piper_executable is not None
    except Exception:
        piper_available = False

    return {
        "piper_tts": {
            "available": piper_available,
            "engine": "piper",
            "description": "On-device text-to-speech using Piper",
        },
        "voice_models": ["piper-default"],
        "status": "online" if piper_available else "degraded",
    }
