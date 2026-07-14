import uuid
from sqlalchemy import String, Integer, ForeignKey, DateTime, UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.models.base import Base

class UploadSession(Base):
    __tablename__ = "upload_sessions"

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
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    upload_id: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    bucket: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    object_key: Mapped[str] = mapped_column(
        String,
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
    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="UPLOADING"
    )
    parts_info: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list
    )
    expires_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
