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
