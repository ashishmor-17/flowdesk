from pydantic import BaseModel, EmailStr
import uuid

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