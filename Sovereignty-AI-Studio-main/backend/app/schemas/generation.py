from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.schemas.media import Media


class GenerationBase(BaseModel):
    generation_type: str
    prompt: str
    parameters: Optional[Dict[str, Any]] = None


class GenerationCreate(GenerationBase):
    project_id: Optional[int] = None


class GenerationUpdate(BaseModel):
    status: Optional[str] = None
    result: Optional[str] = None
    error_message: Optional[str] = None
    processing_time: Optional[float] = None
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None


class GenerationInDB(GenerationBase):
    id: int
    ai_service: str
    status: str
    result: Optional[str]
    processing_time: Optional[float]
    error_message: Optional[str]
    retry_count: int
    tokens_used: Optional[int]
    cost_usd: Optional[float]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    user_id: int
    project_id: Optional[int]

    class Config:
        from_attributes = True


class Generation(GenerationInDB):
    media_files: List[Media] = []


class GenerationListItem(BaseModel):
    id: int
    generation_type: str
    prompt: str
    status: str
    created_at: datetime
    processing_time: Optional[float]

    class Config:
        from_attributes = True
