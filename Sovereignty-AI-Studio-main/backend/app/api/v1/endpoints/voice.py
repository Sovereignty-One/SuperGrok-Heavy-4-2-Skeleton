"""
Voice interaction API endpoints.
Provides voice chat and TTS capabilities using Piper and Coqui TTS.
No Google / No Meta — fully on-device, 127.0.0.1 only.
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
    engine: str = "piper"
    speed: float = 1.0


class VoiceResponse(BaseModel):
    status: str
    message: str
    audio_file: Optional[str] = None
    voice_model: str = "piper-default"
    engine: str = "piper"


@router.post("/speak", response_model=VoiceResponse)
async def text_to_speech(request: VoiceRequest):
    """
    Convert text to speech using Piper or Coqui TTS (on-device only).

    Set ``engine`` to ``"piper"`` or ``"coqui"`` to choose the TTS backend.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    if request.engine == "coqui":
        return await _speak_coqui(request)
    return await _speak_piper(request)


async def _speak_piper(request: VoiceRequest) -> VoiceResponse:
    """Piper TTS path."""
    try:
        from app.services.piper_tts_service import piper_service
        audio_file = piper_service.text_to_speech(request.text)
        if audio_file:
            return VoiceResponse(
                status="completed",
                message="Audio generated successfully",
                audio_file=audio_file,
                voice_model=request.voice_model or "piper-default",
                engine="piper",
            )
        return VoiceResponse(
            status="unavailable",
            message="Piper TTS not available. Install piper and configure PIPER_MODEL_PATH.",
            engine="piper",
        )
    except Exception as e:
        logger.error("Piper TTS error: %s", e)
        return VoiceResponse(
            status="error",
            message=f"Piper TTS failed: {e}",
            engine="piper",
        )


async def _speak_coqui(request: VoiceRequest) -> VoiceResponse:
    """Coqui TTS path (open-source, no Google/Meta)."""
    try:
        from app.services.coqui_tts_service import coqui_tts_service
        audio_file = coqui_tts_service.text_to_speech(
            request.text, model_name=request.voice_model,
        )
        if audio_file:
            return VoiceResponse(
                status="completed",
                message="Audio generated via Coqui TTS",
                audio_file=audio_file,
                voice_model=request.voice_model or "coqui-default",
                engine="coqui",
            )
        return VoiceResponse(
            status="unavailable",
            message="Coqui TTS not available. Install coqui-tts.",
            engine="coqui",
        )
    except Exception as e:
        logger.error("Coqui TTS error: %s", e)
        return VoiceResponse(
            status="error",
            message=f"Coqui TTS failed: {e}",
            engine="coqui",
        )


@router.post("/chat", response_model=dict)
async def voice_chat(request: VoiceRequest):
    """
    Voice interaction endpoint.
    Processes text input and returns AI response with optional TTS.
    Supports both Piper and Coqui engines.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    ai_response = f"Acknowledged: {request.text}"

    result = {
        "input": request.text,
        "response": ai_response,
        "audio_file": None,
        "engine": request.engine,
        "status": "completed",
    }

    try:
        if request.engine == "coqui":
            from app.services.coqui_tts_service import coqui_tts_service
            audio_file = coqui_tts_service.text_to_speech(ai_response)
        else:
            from app.services.piper_tts_service import piper_service
            audio_file = piper_service.text_to_speech(ai_response)
        if audio_file:
            result["audio_file"] = audio_file
    except Exception as e:
        logger.warning("Voice chat TTS failed (%s): %s", request.engine, e)

    return result


@router.get("/status", response_model=dict)
async def voice_status():
    """Check voice system status — Piper + Coqui engines."""
    try:
        from app.services.piper_tts_service import piper_service
        piper_available = piper_service.piper_executable is not None
    except Exception:
        piper_available = False

    try:
        from app.services.coqui_tts_service import coqui_tts_service
        coqui_available = coqui_tts_service.is_available()
        coqui_models = coqui_tts_service.get_available_models()
    except Exception:
        coqui_available = False
        coqui_models = []

    return {
        "piper_tts": {
            "available": piper_available,
            "engine": "piper",
            "description": "On-device TTS using Piper (open-source)",
        },
        "coqui_tts": {
            "available": coqui_available,
            "engine": "coqui",
            "description": "On-device TTS using Coqui (Mozilla-licensed, no Google/Meta)",
            "models": coqui_models,
        },
        "voice_models": ["piper-default", "coqui-default"],
        "status": "online" if (piper_available or coqui_available) else "degraded",
        "no_cloud": True,
    }
