import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class TimeEntryCreate(BaseModel):
    minutes: int = Field(..., gt=0)
    description: str | None = None

class TimeEntryResponse(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    org_id: uuid.UUID
    user_id: uuid.UUID
    minutes: int
    description: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
