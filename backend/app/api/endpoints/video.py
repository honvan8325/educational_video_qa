from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Form,
)
from typing import List
import json
from pydantic import ValidationError

from app.schemas.video import VideoResponse
from app.schemas.context_unit import ContextUnitData
from app.models.user import User
from app.api.deps import get_current_user
from app.services.video_service import (
    upload_video,
    list_videos,
    get_video,
    delete_video,
)

router = APIRouter()


@router.post(
    "/{workspace_id}/videos",
    response_model=VideoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_video_endpoint(
    workspace_id: str,
    video_file: UploadFile = File(...),
    context_units: str = Form(...),
    current_user: User = Depends(get_current_user),
):
    if not video_file.content_type.startswith("video/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Video file must be a video",
        )

    # Parse and validate context_units JSON string
    try:
        context_units_list = json.loads(context_units)
        context_units_data = [ContextUnitData(**item) for item in context_units_list]
    except (json.JSONDecodeError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid context_units format: {str(e)}",
        )

    video_response = await upload_video(
        workspace_id, str(current_user.id), video_file, context_units_data
    )

    return video_response


@router.get("/{workspace_id}/videos", response_model=List[VideoResponse])
async def list_videos_endpoint(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
):
    """List all videos in a workspace."""
    return await list_videos(workspace_id, str(current_user.id))


@router.get(
    "/{workspace_id}/videos/{video_id}",
    response_model=VideoResponse,
)
async def get_video_endpoint(
    workspace_id: str,
    video_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get a specific video by ID."""
    return await get_video(video_id, workspace_id, str(current_user.id))


@router.delete("/{workspace_id}/videos/{video_id}")
async def delete_video_endpoint(
    workspace_id: str,
    video_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a video and its related resources."""
    return await delete_video(video_id, workspace_id, str(current_user.id))
