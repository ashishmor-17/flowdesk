import uuid
import re
from typing import Any
from datetime import datetime
from pydantic import BaseModel, field_validator
from pydantic import EmailStr

from app.core.enums import UserRole

class OrganizationBase(BaseModel):
    name: str
    slug: str | None = None

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    created_at: datetime

    class Config:
        from_attributes= True

class InvitationCreate(BaseModel):
    email: EmailStr
    role: UserRole

    @field_validator("role", mode="before")
    @classmethod
    def normalize_role(cls, v: Any) -> str:
        if isinstance(v, str):
            return v.lower()
        return v
    
class InvitationResponse(BaseModel):
    invitation_id: uuid.UUID
    invited_email: str
    expires_at: datetime

    class Config:
        from_attributes= True

class AcceptInviteRequest(BaseModel):
    token: str

class AcceptInviteResponse(BaseModel):
    message: str
    org_id: uuid.UUID
    role: str

class OrgMemberResponse(BaseModel):
    user_id: uuid.UUID
    full_name: str
    email: str
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True

class OrgMembersListResponse(BaseModel):
    members: list[OrgMemberResponse]

class UpdateMemberRoleRequest(BaseModel):
    role: UserRole
    action_for_prev_owner: str | None = "admin"

    @field_validator("role", mode="before")
    @classmethod
    def normalize_role(cls, v: Any) -> str:
        if isinstance(v, str):
            return v.lower()
        return v

