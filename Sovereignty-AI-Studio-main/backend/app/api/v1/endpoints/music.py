"""
Music generation API endpoints.
Provides music composition and genre-based generation.
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class MusicRequest(BaseModel):
    prompt: str
    genre: str = "ambient"
    duration_seconds: int = 60
    bpm: Optional[int] = None


@router.post("/compose", response_model=dict, status_code=201)
async def compose_music(request: MusicRequest):
    """
    Create a music composition request.

    Supported genres: ambient, electronic, classical, lo-fi, cinematic, focus
    """
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    valid_genres = {"ambient", "electronic", "classical", "lo-fi", "cinematic", "focus"}
    if request.genre not in valid_genres:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid genre. Must be one of: {valid_genres}",
        )

    from app.services.music_service import music_service
    composition = music_service.create_composition(
        prompt=request.prompt,
        genre=request.genre,
        duration_seconds=request.duration_seconds,
        bpm=request.bpm,
    )
    return composition


@router.get("/", response_model=list)
async def list_compositions(limit: int = Query(50, ge=1, le=100)):
    """List all music compositions."""
    from app.services.music_service import music_service
    return music_service.list_compositions(limit)


@router.get("/genres", response_model=dict)
async def get_genres():
    """Get all supported music genres."""
    from app.services.music_service import music_service
    return {"genres": music_service.get_genres()}


@router.get("/{composition_id}", response_model=dict)
async def get_composition(composition_id: int):
    """Get a specific composition by ID."""
    from app.services.music_service import music_service
    composition = music_service.get_composition(composition_id)
    if not composition:
        raise HTTPException(status_code=404, detail="Composition not found")
    return composition
