import uuid
from sqlalchemy import String, Integer, ForeignKey, DateTime, UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.models.base import Base

class MultipartUpload(Base):
    __tablename__ = "multipart_uploads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False
    )
    filename: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    storage_backend: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    s3_upload_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )
    parts_info: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
