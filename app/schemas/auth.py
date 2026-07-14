from pydantic import BaseModel, EmailStr
import uuid
from datetime import datetime

class TokenResponse(BaseModel):
    user_id: uuid.UUID
    email: str
    access_token: str
    refresh_token: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

class LogoutRequest(BaseModel):
    refresh_token: str

class APITokenCreate(BaseModel):
    name: str
    expiry_days: int = 30

class APITokenCreatedResponse(BaseModel):
    id: uuid.UUID
    name: str
    raw_token: str
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class APITokenResponse(BaseModel):
    id: uuid.UUID
    name: str
    token_hash_masked: str
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True
