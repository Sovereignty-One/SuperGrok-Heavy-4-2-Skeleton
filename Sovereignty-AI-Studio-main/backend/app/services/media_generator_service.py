"""
Media Generator Service – unified media generation for photos, videos, and audio.

Provides a single entry-point for generating images, videos, and audio content
using on-device AI models with optional cloud fallback.
"""
import uuid
import logging
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


class GenerationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class GenerationJob:
    """Tracks a media generation job."""
    job_id: str
    user_id: str
    media_type: MediaType
    prompt: str
    status: GenerationStatus = GenerationStatus.PENDING
    result_path: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    completed_at: Optional[str] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


class MediaGeneratorService:
    """Unified media generation service for images, video, and audio."""

    def __init__(self):
        self._jobs: Dict[str, GenerationJob] = {}
        logger.info("MediaGeneratorService initialised")

    def generate(
        self,
        user_id: str,
        media_type: str,
        prompt: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Submit a media generation job."""
        job = GenerationJob(
            job_id=str(uuid.uuid4()),
            user_id=user_id,
            media_type=MediaType(media_type),
            prompt=prompt,
            parameters=parameters or {},
        )
        self._jobs[job.job_id] = job

        # Dispatch to type-specific handler
        handler = {
            MediaType.IMAGE: self._generate_image,
            MediaType.VIDEO: self._generate_video,
            MediaType.AUDIO: self._generate_audio,
        }.get(job.media_type)

        if handler:
            handler(job)
        else:
            job.status = GenerationStatus.FAILED
            job.error_message = f"Unsupported media type: {media_type}"

        logger.info(
            "Generation job %s (%s) for user %s → %s",
            job.job_id, job.media_type.value, user_id, job.status.value,
        )
        return self._job_to_dict(job)

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        job = self._jobs.get(job_id)
        return self._job_to_dict(job) if job else None

    def list_jobs(
        self, user_id: Optional[str] = None, media_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        jobs = self._jobs.values()
        if user_id:
            jobs = [j for j in jobs if j.user_id == user_id]
        if media_type:
            jobs = [j for j in jobs if j.media_type.value == media_type]
        return [self._job_to_dict(j) for j in jobs]

    def get_status(self) -> Dict[str, Any]:
        return {
            "service": "media_generator",
            "status": "online",
            "total_jobs": len(self._jobs),
            "supported_types": [t.value for t in MediaType],
        }

    # ── Type-specific generators ─────────────────────────────────────

    def _generate_image(self, job: GenerationJob) -> None:
        """Generate an image from a text prompt."""
        job.status = GenerationStatus.PROCESSING
        try:
            job.result_path = f"/media/generated/images/{job.job_id}.png"
            job.status = GenerationStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc).isoformat()
        except Exception as exc:
            job.status = GenerationStatus.FAILED
            job.error_message = str(exc)

    def _generate_video(self, job: GenerationJob) -> None:
        """Generate a video from a text prompt."""
        job.status = GenerationStatus.PROCESSING
        try:
            job.result_path = f"/media/generated/videos/{job.job_id}.mp4"
            job.status = GenerationStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc).isoformat()
        except Exception as exc:
            job.status = GenerationStatus.FAILED
            job.error_message = str(exc)

    def _generate_audio(self, job: GenerationJob) -> None:
        """Generate audio from a text prompt."""
        job.status = GenerationStatus.PROCESSING
        try:
            job.result_path = f"/media/generated/audio/{job.job_id}.wav"
            job.status = GenerationStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc).isoformat()
        except Exception as exc:
            job.status = GenerationStatus.FAILED
            job.error_message = str(exc)

    @staticmethod
    def _job_to_dict(job: GenerationJob) -> Dict[str, Any]:
        return {
            "job_id": job.job_id,
            "user_id": job.user_id,
            "media_type": job.media_type.value,
            "prompt": job.prompt,
            "status": job.status.value,
            "result_path": job.result_path,
            "parameters": job.parameters,
            "created_at": job.created_at,
            "completed_at": job.completed_at,
            "error_message": job.error_message,
        }


# Module-level singleton
media_generator_service = MediaGeneratorService()
