from pydantic import BaseModel


class ContextUnitData(BaseModel):

    text: str
    start_time: float
    end_time: float


class ContextUnitResponse(BaseModel):
    """Schema for context unit in API responses."""

    id: str
    video_id: str
    video_path: str
    text: str
    start_time: float
    end_time: float

    class Config:
        from_attributes = True
