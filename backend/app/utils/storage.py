import os
import shutil
from pathlib import Path
from typing import Tuple, Optional
from fastapi import UploadFile
import cv2
from app.config import get_settings

settings = get_settings()


def ensure_upload_dir():
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def ensure_thumbnail_dir():
    thumbnail_dir = Path("./storage/thumbnails")
    thumbnail_dir.mkdir(parents=True, exist_ok=True)
    return thumbnail_dir


async def save_video_file(workspace_id: str, file: UploadFile) -> Tuple[str, int]:
    upload_dir = ensure_upload_dir()
    workspace_dir = upload_dir / workspace_id
    workspace_dir.mkdir(parents=True, exist_ok=True)

    file_path = workspace_dir / file.filename
    file_size = 0

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        file_size = file_path.stat().st_size

    return str(file_path).replace("\\", "/"), file_size


def delete_video_file(file_path: str):
    if os.path.exists(file_path):
        os.remove(file_path)


def delete_video_files_batch(file_paths: list[str]):
    """Delete multiple video files from storage (batch operation)."""
    for file_path in file_paths:
        if os.path.exists(file_path):
            os.remove(file_path)


def delete_workspace_files(workspace_id: str):
    upload_dir = Path(settings.upload_dir)
    workspace_dir = upload_dir / workspace_id
    if workspace_dir.exists():
        shutil.rmtree(workspace_dir)

    # Also delete thumbnails
    thumbnail_dir = Path("./storage/thumbnails") / workspace_id
    if thumbnail_dir.exists():
        shutil.rmtree(thumbnail_dir)


def extract_video_thumbnail(
    video_path: str, workspace_id: str, video_id: str
) -> Optional[str]:
    try:
        thumbnail_dir = ensure_thumbnail_dir()
        workspace_thumbnail_dir = thumbnail_dir / workspace_id
        workspace_thumbnail_dir.mkdir(parents=True, exist_ok=True)

        thumbnail_filename = f"{video_id}.jpg"
        thumbnail_path = workspace_thumbnail_dir / thumbnail_filename

        # Open video and extract frame at 1 second
        cap = cv2.VideoCapture(video_path)
        duration_ms = (
            cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS) * 1000
        )
        midpoint_ms = duration_ms / 2
        cap.set(cv2.CAP_PROP_POS_MSEC, midpoint_ms)  # 1 second
        success, frame = cap.read()

        if success:
            # Save as JPEG with 85% quality
            cv2.imwrite(str(thumbnail_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            cap.release()
            return str(thumbnail_path), duration_ms / 1000
        else:
            cap.release()
            return None, duration_ms / 1000

    except Exception as e:
        print(f"Error extracting thumbnail: {e}")
        return None
