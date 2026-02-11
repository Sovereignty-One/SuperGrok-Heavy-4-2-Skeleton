from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MediaBase(BaseModel):
    filename: str
    original_filename: Optional[str] = None
    file_type: str
    mime_type: str
    file_size: int
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    alt_text: Optional[str] = None


class MediaCreate(MediaBase):
    file_path: str
    project_id: Optional[int] = None
    generation_id: Optional[int] = None


class MediaUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    alt_text: Optional[str] = None
    is_processed: Optional[bool] = None
    processing_status: Optional[str] = None
    file_url: Optional[str] = None


class MediaInDB(MediaBase):
    id: int
    file_path: str
    file_url: Optional[str]
    is_processed: bool
    processing_status: str
    storage_provider: str
    storage_bucket: Optional[str]
    storage_key: Optional[str]
    created_at: datetime
    updated_at: datetime
    project_id: Optional[int]
    generation_id: Optional[int]

    class Config:
        from_attributes = True


class Media(MediaInDB):
    pass


class MediaListItem(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    created_at: datetime

    class Config:
        from_attributes = True
