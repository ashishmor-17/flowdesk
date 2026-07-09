import uuid

from sqlalchemy import String, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class TaskLabel(Base, TimestampMixin):
    __tablename__ = "task_labels"

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
    label: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    task = relationship("Task", back_populates="labels")

    __table_args__ = (
        Index("ix_task_labels_task_id", "task_id"),
    )