from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class VideoResponse(BaseModel):
    """Schema for video response."""

    id: str
    workspace_id: str
    filename: str
    file_path: str
    file_size: int
    duration: Optional[float] = None
    thumbnail_path: Optional[str] = None
    processing_status: str
    created_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
