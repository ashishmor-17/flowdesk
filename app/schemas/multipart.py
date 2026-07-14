import uuid
from datetime import datetime
from pydantic import BaseModel

class UploadSessionInitiateRequest(BaseModel):
    filename: str
    file_size: int

class UploadSessionInitiateResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    upload_id: str
    bucket: str
    object_key: str
    status: str
    expires_at: datetime
    created_at: datetime

class UploadSessionPartResponse(BaseModel):
    part_number: int
    status: str

class UploadSessionProgressResponse(BaseModel):
    id: uuid.UUID
    filename: str
    file_size: int
    parts_uploaded: list[int]
    expires_at: datetime
