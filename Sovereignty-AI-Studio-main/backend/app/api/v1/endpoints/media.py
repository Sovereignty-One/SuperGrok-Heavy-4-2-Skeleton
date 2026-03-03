"""
Media API endpoints for file management.
Handles photos, videos, audio files, and documents.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory store for demo (production uses database)
_media_files = []
_next_id = 1


@router.get("/", response_model=list)
async def list_media(
    file_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
):
    """
    List all media files with optional filtering.

    Supported file_type values: image, audio, video, document
    """
    results = _media_files
    if file_type:
        valid_types = {"image", "audio", "video", "document"}
        if file_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file_type. Must be one of: {valid_types}",
            )
        results = [m for m in results if m["file_type"] == file_type]
    return results[-limit:]


@router.get("/{media_id}", response_model=dict)
async def get_media(media_id: int):
    """Get a specific media file by ID."""
    for m in _media_files:
        if m["id"] == media_id:
            return m
    raise HTTPException(status_code=404, detail="Media file not found")


@router.get("/types/supported", response_model=dict)
async def get_supported_media_types():
    """Get all supported media types and their capabilities."""
    return {
        "types": {
            "image": {
                "description": "Photos and images (PNG, JPEG, WebP, SVG)",
                "extensions": [".png", ".jpg", ".jpeg", ".webp", ".svg"],
                "max_size_mb": 50,
            },
            "audio": {
                "description": "Audio files (WAV, MP3, OGG, FLAC)",
                "extensions": [".wav", ".mp3", ".ogg", ".flac"],
                "max_size_mb": 100,
            },
            "video": {
                "description": "Video files (MP4, WebM, MOV)",
                "extensions": [".mp4", ".webm", ".mov"],
                "max_size_mb": 500,
            },
            "document": {
                "description": "Documents (PDF, TXT, MD)",
                "extensions": [".pdf", ".txt", ".md"],
                "max_size_mb": 25,
            },
        }
    }
