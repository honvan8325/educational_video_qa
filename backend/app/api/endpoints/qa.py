from fastapi import APIRouter, Depends
from typing import List

from app.schemas.qa import QuestionRequest, AnswerResponse, QAResponse
from app.schemas.context_unit import ContextUnitResponse
from app.models.user import User
from app.api.deps import get_current_user
from app.services.qa_service import (
    ask_question,
    get_qa_history,
    delete_all_qa_records,
    delete_qa_record,
)

router = APIRouter()


@router.post("/{workspace_id}/ask", response_model=AnswerResponse)
async def ask_question_endpoint(
    workspace_id: str,
    question_data: QuestionRequest,
    current_user: User = Depends(get_current_user),
):
    question, answer, context_units, response_time = await ask_question(
        workspace_id,
        str(current_user.id),
        question_data.question,
        question_data.video_ids,
        question_data.retriever_type,
        question_data.generator_type,
        question_data.embedding_model,
        question_data.use_reranker,
        question_data.use_history,
        question_data.history_count,
    )

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
        response_time=response_time,
    )


@router.get("/{workspace_id}/history", response_model=List[QAResponse])
async def get_qa_history_endpoint(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
):
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
            response_time=qa.response_time,
            created_at=qa.created_at,
        )
        for qa, context_units in qas_with_contexts
    ]


@router.delete("/{workspace_id}/history")
async def delete_qa_history_endpoint(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
):
    await delete_all_qa_records(workspace_id, str(current_user.id))
    return {"detail": "Q&A history deleted successfully."}


@router.delete("/{workspace_id}/history/{qa_id}")
async def delete_qa_record_endpoint(
    workspace_id: str,
    qa_id: str,
    current_user: User = Depends(get_current_user),
):
    await delete_qa_record(workspace_id, qa_id, str(current_user.id))
    return {"detail": "Q&A record deleted successfully."}
