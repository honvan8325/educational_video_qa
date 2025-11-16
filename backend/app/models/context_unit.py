from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class ContextUnit(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    video_id: str
    video_path: str
    text: str  # Refined text for embedding and search
    start_time: float
    end_time: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        populate_by_name = True
