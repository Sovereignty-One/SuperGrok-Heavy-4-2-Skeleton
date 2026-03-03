"""
Generation API endpoints for media, voice, music, and content generation.
Supports text, image, audio, video generation types with Piper TTS integration.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from app.schemas.generation import (
    GenerationCreate,
    Generation,
    GenerationListItem,
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory store for demo (production uses database)
_generations = []
_next_id = 1


@router.post("/", response_model=dict, status_code=201)
async def create_generation(
    generation: GenerationCreate,
    speak: bool = Query(False, description="Use Piper TTS for audio output"),
):
    """
    Create a new generation request.

    Supported generation_type values: text, image, audio, video, music
    """
    global _next_id

    valid_types = {"text", "image", "audio", "video", "music"}
    if generation.generation_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid generation_type. Must be one of: {valid_types}",
        )

    gen_record = {
        "id": _next_id,
        "generation_type": generation.generation_type,
        "prompt": generation.prompt,
        "parameters": generation.parameters,
        "status": "pending",
        "ai_service": "piper" if generation.generation_type == "audio" else "sovereign",
        "result": None,
        "project_id": generation.project_id,
    }
    _generations.append(gen_record)
    _next_id += 1

    # If TTS requested for audio generation, invoke Piper
    if speak and generation.generation_type in ("audio", "text"):
        try:
            from app.services.piper_tts_service import piper_service
            audio_file = piper_service.text_to_speech(generation.prompt)
            if audio_file:
                gen_record["status"] = "completed"
                gen_record["result"] = audio_file
        except Exception as e:
            logger.warning(f"Piper TTS generation failed: {e}")

    return {
        "id": gen_record["id"],
        "status": gen_record["status"],
        "generation_type": gen_record["generation_type"],
        "message": f"Generation request created for {generation.generation_type}",
    }


@router.get("/", response_model=list)
async def list_generations(
    generation_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
):
    """List all generation requests with optional filtering."""
    results = _generations
    if generation_type:
        results = [g for g in results if g["generation_type"] == generation_type]
    if status:
        results = [g for g in results if g["status"] == status]
    return results[-limit:]


@router.get("/{generation_id}", response_model=dict)
async def get_generation(generation_id: int):
    """Get a specific generation by ID."""
    for gen in _generations:
        if gen["id"] == generation_id:
            return gen
    raise HTTPException(status_code=404, detail="Generation not found")


@router.get("/types/supported", response_model=dict)
async def get_supported_types():
    """Get all supported generation types and their capabilities."""
    return {
        "types": {
            "text": {
                "description": "Text content generation",
                "ai_service": "sovereign",
                "supports_tts": True,
            },
            "image": {
                "description": "Image generation from text prompts",
                "ai_service": "sovereign",
                "supports_tts": False,
            },
            "audio": {
                "description": "Audio generation using Piper TTS",
                "ai_service": "piper",
                "supports_tts": True,
            },
            "video": {
                "description": "Video content generation",
                "ai_service": "sovereign",
                "supports_tts": False,
            },
            "music": {
                "description": "Music generation and composition",
                "ai_service": "sovereign",
                "supports_tts": False,
            },
        }
    }
