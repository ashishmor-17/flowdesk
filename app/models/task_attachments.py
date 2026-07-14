import uuid
from sqlalchemy import String, Integer, ForeignKey, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

class TaskAttachment(Base, TimestampMixin):
    __tablename__ = "task_attachments"

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
    content_type: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    size: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    etag: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    task = relationship("Task", back_populates="attachments")
    uploader = relationship("User")
