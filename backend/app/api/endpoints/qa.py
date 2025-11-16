from fastapi import APIRouter, Depends
from typing import List

from app.schemas.qa import QuestionRequest, AnswerResponse, QAResponse
from app.schemas.context_unit import ContextUnitResponse
from app.models.user import User
from app.api.deps import get_current_user
from app.services.qa_service import ask_question, get_qa_history

router = APIRouter()


@router.post("/{workspace_id}/ask", response_model=AnswerResponse)
async def ask_question_endpoint(
    workspace_id: str,
    question_data: QuestionRequest,
    current_user: User = Depends(get_current_user),
):
    question, answer, context_units = await ask_question(
        workspace_id, str(current_user.id), question_data.question, question_data.video_ids
    )

    # Convert ContextUnit models to ContextUnitResponse
    source_contexts = [
        ContextUnitResponse(
            id=cu.id,
            video_id=cu.video_id,
            video_path=cu.video_path,
            text=cu.text,
            start_time=cu.start_time,
            end_time=cu.end_time,
        )
        for cu in context_units
    ]

    return AnswerResponse(
        question=question,
        answer=answer,
        source_contexts=source_contexts,
    )


@router.get("/{workspace_id}/history", response_model=List[QAResponse])
async def get_qa_history_endpoint(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get Q&A history for a workspace."""
    qas_with_contexts = await get_qa_history(workspace_id, str(current_user.id))

    return [
        QAResponse(
            id=qa.id,
            workspace_id=qa.workspace_id,
            question=qa.question,
            answer=qa.answer,
            source_contexts=[
                ContextUnitResponse(
                    id=cu.id,
                    video_id=cu.video_id,
                    video_path=cu.video_path,
                    text=cu.text,
                    start_time=cu.start_time,
                    end_time=cu.end_time,
                )
                for cu in context_units
            ],
            created_at=qa.created_at,
        )
        for qa, context_units in qas_with_contexts
    ]
