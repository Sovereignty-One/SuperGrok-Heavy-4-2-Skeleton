"""
Movie generation API endpoints.
Provides scene-based movie composition and rendering pipeline.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class MovieCreateRequest(BaseModel):
    user_id: str
    title: str
    genre: str = "short_film"
    description: str = ""
    resolution: str = "1920x1080"
    fps: int = 24


class SceneAddRequest(BaseModel):
    prompt: str
    duration_seconds: float = 5.0
    transition: str = "cut"


@router.post("/", response_model=dict, status_code=201)
async def create_movie(request: MovieCreateRequest):
    """Create a new movie project."""
    if not request.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    from app.services.movie_generator_service import movie_generator_service
    return movie_generator_service.create_project(
        user_id=request.user_id,
        title=request.title,
        genre=request.genre,
        description=request.description,
        resolution=request.resolution,
        fps=request.fps,
    )


@router.get("/status", response_model=dict)
async def movie_status():
    """Get movie generator status and capabilities."""
    from app.services.movie_generator_service import movie_generator_service
    return movie_generator_service.get_status()


@router.get("/{project_id}", response_model=dict)
async def get_movie(project_id: str):
    """Get a specific movie project."""
    from app.services.movie_generator_service import movie_generator_service
    result = movie_generator_service.get_project(project_id)
    if not result:
        raise HTTPException(status_code=404, detail="Movie project not found")
    return result


@router.post("/{project_id}/scenes", response_model=dict)
async def add_scene(project_id: str, request: SceneAddRequest):
    """Add a scene to a movie project's storyboard."""
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Scene prompt cannot be empty")
    from app.services.movie_generator_service import movie_generator_service
    result = movie_generator_service.add_scene(
        project_id=project_id,
        prompt=request.prompt,
        duration_seconds=request.duration_seconds,
        transition=request.transition,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Movie project not found")
    return result


@router.post("/{project_id}/render", response_model=dict)
async def render_movie(project_id: str):
    """Start rendering a movie project."""
    from app.services.movie_generator_service import movie_generator_service
    result = movie_generator_service.render(project_id)
    if not result:
        raise HTTPException(status_code=404, detail="Movie project not found")
    return result


@router.delete("/{project_id}", response_model=dict)
async def delete_movie(project_id: str):
    """Delete a movie project."""
    from app.services.movie_generator_service import movie_generator_service
    if movie_generator_service.delete_project(project_id):
        return {"deleted": True, "project_id": project_id}
    raise HTTPException(status_code=404, detail="Movie project not found")
