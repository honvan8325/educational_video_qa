from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class Workspace(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        populate_by_name = True
