import uuid
from sqlalchemy import ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

class TaskWatcher(Base):
    __tablename__ = "task_watchers"

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint("task_id", "user_id", name="uq_task_watchers_task_user"),
        Index("ix_task_watchers_task_id", "task_id"),
        Index("ix_task_watchers_user_id", "user_id"),
        Index("ix_task_watchers_org_id", "org_id"),
    )
