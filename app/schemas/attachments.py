import uuid
from datetime import datetime
from pydantic import BaseModel

class TaskAttachmentResponse(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    user_id: uuid.UUID
    bucket: str
    object_key: str
    filename: str
    content_type: str
    size: int
    etag: str | None
    created_at: datetime

    class Config:
        from_attributes = True
