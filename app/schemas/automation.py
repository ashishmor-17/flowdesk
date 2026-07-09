import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

from app.core.enums import AutomationTriggerEvent, AutomationActionType

class AutomationRuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    project_id: uuid.UUID | None = None
    trigger_event: AutomationTriggerEvent
    conditions: dict[str, Any] | None = None
    action_type: AutomationActionType
    action_payload: dict[str, Any] | None = None

class AutomationCreateRule(AutomationRuleBase):
    pass

class AutomationRuleUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    project_id: uuid.UUID | None = None
    trigger_event: AutomationTriggerEvent | None = None
    conditions: dict[str, Any] | None = None
    action_type: AutomationActionType | None = None
    action_payload: dict[str, Any] | None = None
    is_active: bool | None = None

class AutomationRuleResponse(AutomationRuleBase):
    id: uuid.UUID
    org_id: uuid.UUID
    is_active: bool
    created_by: uuid.UUID | None
    created_at: datetime
    class Config:
        from_attributes = True

