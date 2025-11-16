from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class WorkspaceCreate(BaseModel):
    name: str

class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None

class WorkspaceResponse(BaseModel):
    id: str
    user_id: str
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
