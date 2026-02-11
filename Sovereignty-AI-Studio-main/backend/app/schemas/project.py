from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.schemas.media import Media


class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None
    project_type: str
    settings: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    is_public: bool = False


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None
    status: Optional[str] = None


class ProjectInDB(ProjectBase):
    id: int
    status: str
    content: Optional[str]
    is_featured: bool
    share_token: Optional[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    owner_id: int

    class Config:
        from_attributes = True


class Project(ProjectInDB):
    media_files: List[Media] = []


class ProjectListItem(BaseModel):
    id: int
    title: str
    description: Optional[str]
    project_type: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
