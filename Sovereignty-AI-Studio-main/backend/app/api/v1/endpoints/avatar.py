"""
Avatar companion API endpoints.
Manages AI avatar state, expressions, and interactions.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class AvatarInteraction(BaseModel):
    message: str


class AvatarMoodUpdate(BaseModel):
    mood: str


class AvatarEEGLink(BaseModel):
    enabled: bool = True


@router.get("/state", response_model=dict)
async def get_avatar_state():
    """Get current avatar companion state."""
    from app.services.avatar_service import avatar_service
    return avatar_service.get_state()


@router.post("/interact", response_model=dict)
async def interact_with_avatar(interaction: AvatarInteraction):
    """Send a message to the avatar companion."""
    if not interaction.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    from app.services.avatar_service import avatar_service
    return avatar_service.interact(interaction.message)


@router.put("/mood", response_model=dict)
async def update_avatar_mood(update: AvatarMoodUpdate):
    """Update avatar mood (neutral, happy, focused, alert, calm)."""
    valid_moods = {"neutral", "happy", "focused", "alert", "calm"}
    if update.mood not in valid_moods:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mood. Must be one of: {valid_moods}",
        )
    from app.services.avatar_service import avatar_service
    return avatar_service.update_mood(update.mood)


@router.post("/eeg-link", response_model=dict)
async def toggle_eeg_link(link: AvatarEEGLink):
    """Link or unlink EEG data to avatar mood."""
    from app.services.avatar_service import avatar_service
    return avatar_service.link_eeg(link.enabled)
