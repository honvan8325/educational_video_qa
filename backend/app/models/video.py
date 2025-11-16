from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class Video(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    workspace_id: str
    filename: str
    file_path: str
    file_size: int
    duration: Optional[float] = None
    thumbnail_path: Optional[str] = None
    processing_status: str = "pending"  # pending, processing, completed, failed
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
