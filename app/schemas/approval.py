import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class ApprovalRequestCreate(BaseModel):
    approver_id: uuid.UUID

class ApprovalRequestDecision(BaseModel):
    status: str = Field(..., description="Must be approved or rejected")
    comment: str | None = None

class ApprovalRequestResponse(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    org_id: uuid.UUID
    requestor_id: uuid.UUID
    approver_id: uuid.UUID
    status: str
    comment: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
