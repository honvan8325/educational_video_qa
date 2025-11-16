from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse
from app.models.user import User
from app.api.deps import get_current_user
from app.services.workspace_service import (
    create_workspace,
    list_workspaces,
    get_workspace,
    update_workspace,
    delete_workspace,
)

router = APIRouter()


@router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace_endpoint(
    workspace_data: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
):
    return await create_workspace(workspace_data, str(current_user.id))


@router.get("/", response_model=List[WorkspaceResponse])
async def list_workspaces_endpoint(
    current_user: User = Depends(get_current_user),
):
    return await list_workspaces(str(current_user.id))


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace_endpoint(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
):
    return await get_workspace(workspace_id, str(current_user.id))


@router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace_endpoint(
    workspace_id: str,
    workspace_data: WorkspaceUpdate,
    current_user: User = Depends(get_current_user),
):
    return await update_workspace(workspace_id, workspace_data, str(current_user.id))


@router.delete("/{workspace_id}")
async def delete_workspace_endpoint(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
):
    return await delete_workspace(workspace_id, str(current_user.id))
