import time
from typing import List, Tuple, Dict, Optional
from fastapi import HTTPException, status
from app.database import get_database
from app.models.qa import QA
from app.models.context_unit import ContextUnit
from app.services.rag_service import rag_service
from app.utils.db_helpers import prepare_id_filter, convert_objectid_to_str
from datetime import datetime, timezone


async def fetch_context_units_by_ids(db, context_ids: List[str]) -> List[ContextUnit]:

    if not context_ids:
        return []

    try:
        object_ids = [prepare_id_filter(cid) for cid in context_ids if cid]
        contexts = await db.context_units.find({"_id": {"$in": object_ids}}).to_list(
            None
        )

        # Convert and maintain order
        id_to_context = {str(ctx["_id"]): ctx for ctx in contexts}
        ordered_contexts = []

        for cid in context_ids:
            if cid and cid in id_to_context:
                ctx_dict = convert_objectid_to_str(id_to_context[cid])
                ordered_contexts.append(ContextUnit(**ctx_dict))

        return ordered_contexts
    except Exception as e:
        print(f"Error fetching context units: {e}")
        return []


async def ask_question(
    workspace_id: str,
    user_id: str,
    question: str,
    video_ids: Optional[List[str]] = None,
    retriever_type: str = "vector",
    generator_type: str = "gemini",
    embedding_model: str = "dangvantuan",
    use_reranker: bool = False,
    use_history: bool = False,
    history_count: int = 3,
) -> Tuple[str, str, List[ContextUnit], float]:
    db = await get_database()

    workspace_dict = await db.workspaces.find_one(
        {"_id": prepare_id_filter(workspace_id), "user_id": user_id}
    )

    if not workspace_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    videos_count = await db.videos.count_documents(
        {"workspace_id": workspace_id, "processing_status": "completed"}
    )

    if videos_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No processed videos available in this workspace",
        )

    conversation_history = None
    if use_history and history_count > 0:
        history_records = (
            await db.qa.find({"workspace_id": workspace_id})
            .sort("created_at", -1)
            .limit(history_count)
            .to_list(history_count)
        )

        conversation_history = [
            {"question": record["question"], "answer": record["answer"]}
            for record in reversed(history_records)
        ]

    # Measure response time
    start_time = time.time()
    answer, context_ids = await rag_service.answer_question(
        workspace_id,
        question,
        video_ids,
        retriever_type,
        generator_type,
        embedding_model,
        use_reranker,
        conversation_history,
    )
    response_time = time.time() - start_time

    # Save Q&A record
    qa = QA(
        workspace_id=workspace_id,
        question=question,
        answer=answer,
        source_context_ids=context_ids,
        response_time=response_time,
    )
    qa_dict = qa.model_dump(by_alias=True, exclude={"id"})
    result = await db.qa.insert_one(qa_dict)

    await db.workspaces.update_one(
        {"_id": prepare_id_filter(workspace_id)},
        {"$set": {"updated_at": datetime.now(timezone.utc)}},
    )

    # Fetch full context unit data for response
    context_units = await fetch_context_units_by_ids(db, context_ids)

    return question, answer, context_units, response_time


async def get_qa_history(
    workspace_id: str, user_id: str
) -> List[Tuple[QA, List[ContextUnit]]]:

    db = await get_database()

    # Verify workspace exists and user has access
    workspace_dict = await db.workspaces.find_one(
        {"_id": prepare_id_filter(workspace_id), "user_id": user_id}
    )

    if not workspace_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    # Get Q&A history from database
    qa_cursor = db.qa.find({"workspace_id": workspace_id}).sort("created_at", 1)
    qas_with_contexts = []

    async for qa_dict in qa_cursor:
        qa_dict = convert_objectid_to_str(qa_dict)
        qa = QA(**qa_dict)

        context_units = await fetch_context_units_by_ids(db, qa.source_context_ids)

        qas_with_contexts.append((qa, context_units))

    return qas_with_contexts


async def delete_all_qa_records(workspace_id: str, user_id: str) -> None:
    db = await get_database()

    workspace_dict = await db.workspaces.find_one(
        {"_id": prepare_id_filter(workspace_id), "user_id": user_id}
    )

    if not workspace_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    await db.qa.delete_many({"workspace_id": workspace_id})


async def delete_qa_record(workspace_id: str, qa_id: str, user_id: str) -> None:
    db = await get_database()

    workspace_dict = await db.workspaces.find_one(
        {"_id": prepare_id_filter(workspace_id), "user_id": user_id}
    )

    if not workspace_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    result = await db.qa.delete_one(
        {
            "_id": prepare_id_filter(qa_id),
            "workspace_id": workspace_id,
        }
    )

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Q&A record not found",
        )
