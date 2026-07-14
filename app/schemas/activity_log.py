import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class ActivityLogResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    actor_id: uuid.UUID | None
    action: str
    entity_type: str
    entity_id: uuid.UUID
    metadata: dict | None = Field(validation_alias="meta_data")
    created_at: datetime

    class Config:
        from_attributes = True
