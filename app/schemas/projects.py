import uuid
import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, field_serializer
from app.core.enums import ProjectStatus

class ProjectBase(BaseModel):
    name: str
    description: str | None = None
    color: str | None = None

    @field_validator("color")
    @classmethod
    def validate_hex_color(cls, v: str | None) -> str | None:
        if v is not None:
            if not re.match(r"^#[0-9a-fA-F]{6}$", v):
                raise ValueError(
                    "Color must be a valid hex color starting with '#'"
                )
        return v

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: uuid.UUID
    org_id: uuid.UUID
    status: ProjectStatus
    created_by: uuid.UUID
    created_at : datetime
    updated_at: datetime

    @field_serializer("status")
    def serialize_status(self, status: ProjectStatus) -> str:
        return status.value.upper()

    class Config:
        from_attributes = True

class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]

class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    color: str | None = None

    @field_validator("color")
    @classmethod
    def validate_hex_color(cls, v: str | None) -> str | None:
        if v is not None:
            if not re.match(r"^#[0-9a-fA-F]{6}$", v):
                raise ValueError(
                    "Color must be a valid hex color starting with '#'"
                )
        return v
    
class ProjectArchiveResponse(BaseModel):
    id: uuid.UUID
    status: str

