from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from app.schemas.context_unit import ContextUnitResponse


class QuestionRequest(BaseModel):
    """Schema for asking a question."""

    question: str
    video_ids: Optional[List[str]] = None  # Filter to specific videos, None = all videos


class AnswerResponse(BaseModel):
    """Schema for answer response."""

    question: str
    answer: str
    source_contexts: List[ContextUnitResponse]


class QAResponse(BaseModel):
    """Schema for Q&A record response."""

    id: str
    workspace_id: str
    question: str
    answer: str
    source_contexts: List[ContextUnitResponse]
    created_at: datetime

    class Config:
        from_attributes = True
