from typing import List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException, status, UploadFile
from bson import ObjectId
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.database import get_database
from app.models.video import Video
from app.models.context_unit import ContextUnit
from app.schemas.video import VideoResponse
from app.schemas.context_unit import ContextUnitData
from app.utils.db_helpers import convert_objectid_to_str, prepare_id_filter
from app.utils.storage import (
    save_video_file,
    delete_video_file,
    delete_video_files_batch,
    extract_video_thumbnail,
)
from app.services.vector_store import vector_store
from app.services.gemini_service import gemini_service

executor = ThreadPoolExecutor(max_workers=2)


async def upload_video(
    workspace_id: str,
    user_id: str,
    video_file: UploadFile,
    context_units_data: List[ContextUnitData],
) -> VideoResponse:

    db = await get_database()

    workspace = await db.workspaces.find_one(
        {"_id": prepare_id_filter(workspace_id), "user_id": user_id}
    )

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )

    file_path, file_size = await save_video_file(workspace_id, video_file)

    video = Video(
        workspace_id=workspace_id,
        filename=video_file.filename,
        file_path=file_path,
        file_size=file_size,
        processing_status="completed",
        processed_at=datetime.now(timezone.utc),
    )

    video_dict = video.model_dump(by_alias=True, exclude={"id"})
    result = await db.videos.insert_one(video_dict)

    video_dict["_id"] = str(result.inserted_id)
    created_video = Video(**video_dict)

    video_id = created_video.id
    video_path = created_video.file_path

    # Extract thumbnail
    thumbnail_path, duration = await asyncio.get_running_loop().run_in_executor(
        executor,
        extract_video_thumbnail,
        file_path,
        workspace_id,
        video_id,
    )

    await db.videos.update_one(
        {"_id": ObjectId(video_id)},
        {"$set": {"thumbnail_path": thumbnail_path, "duration": duration}},
    )
    created_video.thumbnail_path = thumbnail_path
    created_video.duration = duration

    # Refine texts using Gemini before saving
    if context_units_data:
        # Extract original texts
        original_texts = [unit.text.strip() for unit in context_units_data]

        # Create refinement prompts with more transformative instructions to avoid copyright detection
        refine_prompt_template = """Hãy đọc kỹ đoạn nội dung sau (bao gồm visual_text + audio_text). 
Hãy hiểu ý chính và DIỄN GIẢI LẠI HOÀN TOÀN theo cách của bạn, không sao chép.

Nhiệm vụ:
- Trích lọc & tổng hợp các thông tin LIÊN QUAN TỚI BÀI GIẢNG (kiến thức, lý thuyết, công thức, ví dụ, quan hệ, định nghĩa…)
- Giữ NGUYÊN đầy đủ các nội dung học thuật xuất hiện trên slide (ý chính, công thức, thuật ngữ, quan hệ từ vựng…)
- Loại bỏ toàn bộ phần không mang kiến thức: mô tả hình ảnh giảng viên, màu nền, bố cục, logo, intro, filler.
- Ghép audio + slide thành một bản DIỄN GIẢI RÕ RÀNG – LOGIC – TỐI ƯU CHO SEMANTIC SEARCH.
- Viết lại bằng ngôn ngữ tự nhiên, rõ nghĩa, tránh lặp lại văn bản gốc để hạn chế kiểm tra bản quyền.
- Giữ nguyên các ký hiệu toán học, vector, công thức (không được lược bỏ).
- Các ví dụ trên slide (như king–queen, Berlin–Germany, apples–apple+car…) phải được giữ lại đầy đủ.
- Ưu tiên diễn giải theo dạng "giải thích khái niệm + công thức + ví dụ + kết luận".

Đầu ra:
- Một đoạn văn tóm lược – diễn giải mới hoàn toàn, mạch lạc, rõ ràng
- Có thể dùng làm context cho Educational Video QA hoặc semantic RAG search
- Không để sót bất kỳ nội dung kiến thức nào trong đoạn gốc

Nội dung cần diễn giải:
{text}

Nội dung đã diễn giải:
"""

        prompts = [refine_prompt_template.format(text=text) for text in original_texts]

        # Refine all texts in batch
        refined_texts_raw = await gemini_service.generate_contents_batch(prompts)

        # Fallback to original text if refinement failed (None)
        refined_texts = [
            refined if refined is not None else original
            for refined, original in zip(refined_texts_raw, original_texts)
        ]

        # Log refinement results for debugging
        failed_count = sum(1 for r in refined_texts_raw if r is None)
        if failed_count > 0:
            print(
                f"Text refinement: {failed_count}/{len(refined_texts_raw)} texts failed, using original"
            )
    else:
        refined_texts = []

    context_dicts = [
        ContextUnit(
            video_id=video_id,
            video_path=video_path,
            text=refined_text,
            start_time=unit_data.start_time,
            end_time=unit_data.end_time,
        ).model_dump(by_alias=True, exclude={"id"})
        for unit_data, refined_text in zip(context_units_data, refined_texts)
    ]

    if context_dicts:
        result = await db.context_units.insert_many(context_dicts)

        for context_dict, inserted_id in zip(context_dicts, result.inserted_ids):
            context_dict["_id"] = str(inserted_id)

        context_units = [ContextUnit(**context_dict) for context_dict in context_dicts]

        await asyncio.get_running_loop().run_in_executor(
            executor,
            vector_store.add_context_units,
            workspace_id,
            video_id,
            video_path,
            context_units,
        )

    video_response = VideoResponse(
        id=created_video.id,
        workspace_id=created_video.workspace_id,
        filename=created_video.filename,
        file_path=created_video.file_path,
        file_size=created_video.file_size,
        duration=created_video.duration,
        thumbnail_path=created_video.thumbnail_path,
        processing_status=created_video.processing_status,
        created_at=created_video.created_at,
        processed_at=created_video.processed_at,
    )

    return video_response


async def list_videos(workspace_id: str, user_id: str) -> List[VideoResponse]:
    db = await get_database()

    workspace = await db.workspaces.find_one(
        {"_id": prepare_id_filter(workspace_id), "user_id": user_id}
    )

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )

    videos_cursor = db.videos.find({"workspace_id": workspace_id}).sort(
        "created_at", -1
    )
    videos = []

    async for video_dict in videos_cursor:
        video_dict = convert_objectid_to_str(video_dict)
        video = Video(**video_dict)
        videos.append(
            VideoResponse(
                id=video.id,
                workspace_id=video.workspace_id,
                filename=video.filename,
                file_path=video.file_path,
                file_size=video.file_size,
                duration=video.duration,
                thumbnail_path=video.thumbnail_path,
                processing_status=video.processing_status,
                created_at=video.created_at,
                processed_at=video.processed_at,
            )
        )

    return videos


async def get_video(video_id: str, workspace_id: str, user_id: str) -> VideoResponse:
    db = await get_database()

    workspace = await db.workspaces.find_one(
        {"_id": prepare_id_filter(workspace_id), "user_id": user_id}
    )

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )

    video_dict = await db.videos.find_one(
        {"_id": prepare_id_filter(video_id), "workspace_id": workspace_id}
    )

    if not video_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
        )

    video_dict = convert_objectid_to_str(video_dict)
    video = Video(**video_dict)

    return VideoResponse(
        id=video.id,
        workspace_id=video.workspace_id,
        filename=video.filename,
        file_path=video.file_path,
        file_size=video.file_size,
        duration=video.duration,
        thumbnail_path=video.thumbnail_path,
        processing_status=video.processing_status,
        created_at=video.created_at,
        processed_at=video.processed_at,
    )


async def delete_video(video_id: str, workspace_id: str, user_id: str) -> dict:
    db = await get_database()

    workspace = await db.workspaces.find_one(
        {"_id": prepare_id_filter(workspace_id), "user_id": user_id}
    )

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )

    video_dict = await db.videos.find_one(
        {"_id": prepare_id_filter(video_id), "workspace_id": workspace_id}
    )

    if not video_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
        )

    context_ids_to_delete = await db.context_units.find(
        {"video_id": video_id}, {"_id": 1}
    ).to_list(None)

    if context_ids_to_delete:
        context_ids = [str(ctx["_id"]) for ctx in context_ids_to_delete]
        await asyncio.get_running_loop().run_in_executor(
            executor,
            vector_store.delete_context_units,
            workspace_id,
            context_ids,
        )

    await db.context_units.delete_many({"video_id": video_id})

    await asyncio.get_running_loop().run_in_executor(
        executor, delete_video_file, video_dict["file_path"]
    )

    await db.videos.delete_one({"_id": prepare_id_filter(video_id)})

    return {"message": "Video deleted successfully"}


async def delete_videos_batch(workspace_id: str, video_ids: List[str]) -> None:
    if not video_ids:
        return

    db = await get_database()

    video_object_ids = [prepare_id_filter(vid) for vid in video_ids]
    videos = await db.videos.find({"_id": {"$in": video_object_ids}}).to_list(None)

    context_ids_cursor = db.context_units.find(
        {"video_id": {"$in": video_ids}}, {"_id": 1}
    )
    context_ids = [str(ctx["_id"]) async for ctx in context_ids_cursor]

    if context_ids:
        await asyncio.get_running_loop().run_in_executor(
            executor,
            vector_store.delete_context_units,
            workspace_id,
            context_ids,
        )

    await db.context_units.delete_many({"video_id": {"$in": video_ids}})

    file_paths = [v["file_path"] for v in videos]
    if file_paths:
        await asyncio.get_running_loop().run_in_executor(
            executor, delete_video_files_batch, file_paths
        )

    await db.videos.delete_many({"_id": {"$in": video_object_ids}})
