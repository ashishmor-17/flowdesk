import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from app.core.enums import TaskPriority

class SLAPolicyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    priority: TaskPriority
    duration_minutes: int = Field(..., gt=0)

class SLAPolicyResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    name: str
    priority: TaskPriority
    duration_minutes: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
