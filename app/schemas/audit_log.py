import uuid
from datetime import datetime
from pydantic import BaseModel

class AuditLogResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    actor_id: uuid.UUID | None
    action: str
    entity_type: str
    entity_id: uuid.UUID
    old_value: dict | None
    new_value: dict | None
    created_at: datetime

    class Config:
        from_attributes = True
