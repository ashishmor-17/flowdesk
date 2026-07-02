import uuid
from datetime import datetime
from pydantic import BaseModel, Field, model_validator

class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)

class CommentUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)

class CommentResponse(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    org_id: uuid.UUID
    author_id: uuid.UUID
    content: str
    created_at: datetime | None
    edited_at: datetime | None
    deleted_at: datetime | None
    edited: bool = False

    class Config:
        from_attributes = True

    @model_validator(mode="after")
    def process_presentation_logic(self) -> "CommentResponse":
        if self.deleted_at is not None:
            self.content = "[deleted]"
        self.edited = (self.edited_at is not None)

        return self

class CommentsListResponse(BaseModel):
    comments: list[CommentResponse]
    next_cursor: str | None = None

