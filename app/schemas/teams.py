import uuid
from datetime import datetime
from pydantic import BaseModel

class TeamCreate(BaseModel):
    name: str

class TeamResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    name: str
    created_at: datetime

    class Config:
        from_attributes = True

class TeamMemberAdd(BaseModel):
    user_id: uuid.UUID

class TeamMemberResponse(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    user_id: uuid.UUID
    joined_at: datetime

    class Config:
        from_attributes = True
