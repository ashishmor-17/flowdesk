import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel

class NotificationResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    recipient_id: uuid.UUID
    actor_id: uuid.UUID | None = None
    type: str
    entity_type: str | None = None
    entity_id: uuid.UUID | None = None
    payload: dict[str, Any]
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationListResponse(BaseModel):
    notifications: list[NotificationResponse]
    next_cursor: str | None = None
