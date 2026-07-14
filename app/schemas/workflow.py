import uuid
from pydantic import BaseModel, Field

class ProjectStatusCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: str | None = Field(None, max_length=50)
    position: int = Field(0, ge=0)

class ProjectStatusResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    org_id: uuid.UUID
    name: str
    color: str | None
    position: int

    class Config:
        from_attributes = True

class WorkflowRuleCreate(BaseModel):
    from_status: str = Field(..., min_length=1, max_length=100)
    to_status: str = Field(..., min_length=1, max_length=100)

class WorkflowRuleResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    org_id: uuid.UUID
    from_status: str
    to_status: str

    class Config:
        from_attributes = True
