import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class TaskLinkCreate(BaseModel):
    target_task_id: uuid.UUID
    link_type: str = Field(..., min_length=1)

class TaskLinkResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    source_task_id: uuid.UUID
    target_task_id: uuid.UUID
    link_type: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
