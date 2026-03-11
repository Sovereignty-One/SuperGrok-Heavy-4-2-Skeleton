"""
OPAR API endpoints — On-Premises AI Representative.

Provides HTTP routes for creating, customising, and interacting with
OPAR instances.  Every mutation is audit-logged.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Request / Response models ────────────────────────────────────────

class OPARCreateRequest(BaseModel):
    user_id: str
    name: str = "OPAR"
    body_type: str = "human_realistic"
    gender: str = "androgynous"
    voice_engine: str = "piper"
    voice_model: str = "en_US-lessac-medium"
    personality: str = "professional"
    location: str = "living_room"
    appearance_overrides: Optional[Dict[str, Any]] = None


class OPARInteractRequest(BaseModel):
    message: str


class OPARAppearanceUpdate(BaseModel):
    updates: Dict[str, Any]


class OPARLocationUpdate(BaseModel):
    location: str


# ── Endpoints ────────────────────────────────────────────────────────

@router.post("/", response_model=dict, status_code=201)
async def create_opar(request: OPARCreateRequest):
    """Create a new OPAR instance with full 3-D CGI appearance."""
    from app.services.opar_service import opar_service
    return opar_service.create_instance(
        user_id=request.user_id,
        name=request.name,
        body_type=request.body_type,
        gender=request.gender,
        voice_engine=request.voice_engine,
        voice_model=request.voice_model,
        personality=request.personality,
        location=request.location,
        appearance_overrides=request.appearance_overrides,
    )


@router.get("/status", response_model=dict)
async def opar_status():
    """Get OPAR system status and capabilities."""
    from app.services.opar_service import opar_service
    return opar_service.get_status()


@router.get("/{opar_id}", response_model=dict)
async def get_opar(opar_id: str):
    """Get a specific OPAR instance."""
    from app.services.opar_service import opar_service
    result = opar_service.get_instance(opar_id)
    if not result:
        raise HTTPException(status_code=404, detail="OPAR instance not found")
    return result


@router.post("/{opar_id}/interact", response_model=dict)
async def interact_with_opar(opar_id: str, request: OPARInteractRequest):
    """Send a message to an OPAR and receive a response."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    from app.services.opar_service import opar_service
    result = opar_service.interact(opar_id, request.message)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.put("/{opar_id}/appearance", response_model=dict)
async def update_opar_appearance(opar_id: str, request: OPARAppearanceUpdate):
    """Update the 3-D CGI appearance of an OPAR."""
    from app.services.opar_service import opar_service
    result = opar_service.update_appearance(opar_id, request.updates)
    if not result:
        raise HTTPException(status_code=404, detail="OPAR instance not found")
    return result


@router.put("/{opar_id}/location", response_model=dict)
async def update_opar_location(opar_id: str, request: OPARLocationUpdate):
    """Update the in-home location of an OPAR."""
    from app.services.opar_service import opar_service
    result = opar_service.update_location(opar_id, request.location)
    if not result:
        raise HTTPException(status_code=404, detail="OPAR instance not found")
    return result


@router.delete("/{opar_id}", response_model=dict)
async def delete_opar(opar_id: str):
    """Delete an OPAR instance."""
    from app.services.opar_service import opar_service
    if opar_service.delete_instance(opar_id):
        return {"deleted": True, "opar_id": opar_id}
    raise HTTPException(status_code=404, detail="OPAR instance not found")
