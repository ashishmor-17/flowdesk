import uuid
from datetime import date, datetime
from pydantic import BaseModel, Field

from app.core.enums import TaskStatus, TaskPriority

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: date | None = None

class TaskCreate(TaskBase):
    project_id: uuid.UUID

class TaskAssigneeResponse(BaseModel):
    user_id: uuid.UUID
    assigned_at: datetime

    class Config:
        from_attributes = True

class TaskLabelResponse(BaseModel):
    id: uuid.UUID
    name: str
    color: str | None 

    class Config:
        from_attributes = True

class TaskResponse(TaskBase):
    id: uuid.UUID
    project_id: uuid.UUID
    org_id: uuid.UUID
    status: TaskStatus
    created_by: uuid.UUID
    version: int
    created_at: datetime
    updated_at: datetime
    assignees: list[TaskAssigneeResponse] = []
    labels: list[TaskLabelResponse] = []

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
    next_cursor: str | None = None

class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    priority: TaskPriority | None = None
    due_date: date | None = None
    version: int = Field(..., description= "Current version of the task for optimistic locking verification.")

class TaskStatusUpdate(BaseModel):
    status: TaskStatus
    version: int = Field(..., description= "Current version of the task for optimistic locking verification.")

class TaskAssignUpdate(BaseModel):
    user_ids: list[uuid.UUID]

