from typing import List
from datetime import datetime, timezone
from fastapi import HTTPException, status
import asyncio
from app.database import get_database
from app.models.workspace import Workspace
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse
from app.utils.db_helpers import convert_objectid_to_str, prepare_id_filter
from app.services.vector_store import vector_store
from app.utils.storage import delete_workspace_files
from app.services.video_service import delete_videos_batch


async def create_workspace(
    workspace_data: WorkspaceCreate, user_id: str
) -> WorkspaceResponse:
    db = await get_database()

    workspace = Workspace(
        user_id=user_id,
        name=workspace_data.name,
    )

    workspace_dict = workspace.model_dump(by_alias=True, exclude={"id"})
    result = await db.workspaces.insert_one(workspace_dict)
    workspace_dict["id"] = str(result.inserted_id)

    return WorkspaceResponse(**workspace_dict)


async def list_workspaces(user_id: str) -> List[WorkspaceResponse]:
    db = await get_database()

    workspaces_cursor = db.workspaces.find({"user_id": user_id}).sort("updated_at", -1)
    workspaces = []

    async for workspace_dict in workspaces_cursor:
        workspace = Workspace(**convert_objectid_to_str(workspace_dict))
        workspaces.append(
            WorkspaceResponse(
                id=workspace.id,
                user_id=workspace.user_id,
                name=workspace.name,
                created_at=workspace.created_at,
                updated_at=workspace.updated_at,
            )
        )

    return workspaces


async def get_workspace(workspace_id: str, user_id: str) -> WorkspaceResponse:
    db = await get_database()

    workspace_dict = await db.workspaces.find_one(
        {"_id": prepare_id_filter(workspace_id), "user_id": user_id}
    )

    if not workspace_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )

    workspace = Workspace(**convert_objectid_to_str(workspace_dict))
    return WorkspaceResponse(
        id=workspace.id,
        user_id=workspace.user_id,
        name=workspace.name,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )


async def update_workspace(
    workspace_id: str, workspace_data: WorkspaceUpdate, user_id: str
) -> WorkspaceResponse:
    db = await get_database()

    workspace_dict = await db.workspaces.find_one(
        {"_id": prepare_id_filter(workspace_id), "user_id": user_id}
    )

    if not workspace_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )

    update_data = workspace_data.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc)

    await db.workspaces.update_one(
        {"_id": prepare_id_filter(workspace_id)}, {"$set": update_data}
    )

    updated_workspace_dict = await db.workspaces.find_one(
        {"_id": prepare_id_filter(workspace_id)}
    )
    workspace = Workspace(**convert_objectid_to_str(updated_workspace_dict))
    return WorkspaceResponse(
        id=workspace.id,
        user_id=workspace.user_id,
        name=workspace.name,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )


async def clone_workspace(workspace_id: str, user_id: str) -> WorkspaceResponse:
    db = await get_database()

    workspace_dict = await db.workspaces.find_one(
        {"_id": prepare_id_filter(workspace_id), "user_id": user_id}
    )

    if not workspace_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )

    source_workspace = Workspace(**convert_objectid_to_str(workspace_dict))

    new_workspace = Workspace(
        user_id=user_id,
        name=f"{source_workspace.name} (Copy)",
    )

    new_workspace_dict = new_workspace.model_dump(by_alias=True, exclude={"id"})
    result = await db.workspaces.insert_one(new_workspace_dict)
    new_workspace_id = str(result.inserted_id)

    videos = await db.videos.find({"workspace_id": workspace_id}).to_list(None)

    video_id_mapping = {}

    if videos:
        old_video_ids = [str(video["_id"]) for video in videos]

        cloned_videos = []
        for video in videos:
            cloned_video = {
                "workspace_id": new_workspace_id,
                "filename": video["filename"],
                "file_path": video["file_path"],
                "file_size": video["file_size"],
                "duration": video.get("duration"),
                "thumbnail_path": video.get("thumbnail_path"),
                "processing_status": video.get("processing_status", "completed"),
                "created_at": datetime.now(timezone.utc),
                "processed_at": video.get("processed_at"),
            }
            cloned_videos.append(cloned_video)

        if cloned_videos:
            result = await db.videos.insert_many(cloned_videos)
            video_id_mapping = {
                old_id: str(new_id)
                for old_id, new_id in zip(old_video_ids, result.inserted_ids)
            }

    if video_id_mapping:
        old_video_ids = list(video_id_mapping.keys())
        context_units = await db.context_units.find(
            {"video_id": {"$in": old_video_ids}}
        ).to_list(None)

        if context_units:
            cloned_context_units = []
            for context in context_units:
                old_video_id = context["video_id"]
                new_video_id = video_id_mapping.get(old_video_id)

                if new_video_id:
                    cloned_context = {
                        "video_id": new_video_id,
                        "video_path": context["video_path"],
                        "text": context["text"],
                        "start_time": context["start_time"],
                        "end_time": context["end_time"],
                    }
                    cloned_context_units.append(cloned_context)

        if cloned_context_units:
            result = await db.context_units.insert_many(cloned_context_units)

            # Build context_id mapping (old -> new)
            context_id_mapping = {}
            for i, old_context in enumerate(context_units):
                old_id = str(old_context["_id"])
                new_id = str(result.inserted_ids[i])
                context_id_mapping[old_id] = new_id

            # Fast clone vector embeddings (copy embeddings, no re-embedding)
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                vector_store.clone_workspace_collection,
                workspace_id,
                new_workspace_id,
                context_id_mapping,
                video_id_mapping,
            )

    new_workspace_dict["id"] = new_workspace_id
    return WorkspaceResponse(**new_workspace_dict)


async def delete_workspace(workspace_id: str, user_id: str) -> dict:
    db = await get_database()

    workspace_dict = await db.workspaces.find_one(
        {"_id": prepare_id_filter(workspace_id), "user_id": user_id}
    )

    if not workspace_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )

    videos = await db.videos.find({"workspace_id": workspace_id}, {"_id": 1}).to_list(
        None
    )
    video_ids = [str(v["_id"]) for v in videos]

    if video_ids:
        await delete_videos_batch(workspace_id, video_ids)

    await db.qa.delete_many({"workspace_id": workspace_id})

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None, vector_store.delete_workspace_collection, workspace_id
    )
    await loop.run_in_executor(None, delete_workspace_files, workspace_id)

    await db.workspaces.delete_one({"_id": prepare_id_filter(workspace_id)})

    return {"message": "Workspace deleted successfully"}
