from pydantic import BaseModel, EmailStr
import uuid
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str
    first_name: str
    last_name: str | None = None

class PreferencesSchema(BaseModel):
    theme: str | None = None
    language: str | None = None
    timezone: str | None = None
    notifications: dict | None = None

    class Config:
        from_attributes = True

class UserProfileSchema(BaseModel):
    first_name: str
    last_name: str | None = None
    preferences: dict = {}

    class Config:
        from_attributes = True

class UserUpdatePayload(BaseModel):
    preferences: PreferencesSchema

class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str

class UserResponse(UserBase):
    id: uuid.UUID
    full_name: str | None = None
    is_active: bool
    created_at: datetime
    profile: UserProfileSchema | None = None

    class Config:
        from_attributes = True

class MeResponse(UserResponse):
    unread_notifications_count: int
    org_id: uuid.UUID | None = None
    org_name: str | None = None
