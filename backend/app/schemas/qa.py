from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from app.schemas.context_unit import ContextUnitResponse


class QuestionRequest(BaseModel):
    question: str
    video_ids: Optional[List[str]] = None
    retriever_type: str = "vector"
    generator_type: str = "gemini"
    embedding_model: str = "dangvantuan"
    use_reranker: bool = False
    use_history: bool = False
    history_count: int = 3


class AnswerResponse(BaseModel):

    question: str
    answer: str
    source_contexts: List[ContextUnitResponse]
    response_time: float


class QAResponse(BaseModel):

    id: str
    workspace_id: str
    question: str
    answer: str
    source_contexts: List[ContextUnitResponse]
    response_time: float
    created_at: datetime

    class Config:
        from_attributes = True
