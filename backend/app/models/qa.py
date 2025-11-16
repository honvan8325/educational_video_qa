from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field


class QA(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    workspace_id: str
    question: str
    answer: str
    source_context_ids: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        populate_by_name = True
