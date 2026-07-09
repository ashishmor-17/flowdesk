import uuid

from sqlalchemy import ForeignKey, String, Boolean, DateTime, Index, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

class TaskEvent(Base, TimestampMixin):
    __tablename__ = "task_events"

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
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False
    )
    event_type: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    payload: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True
    )
    processed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    task = relationship("Task")
    org = relationship("Organization", back_populates="task_events")
    actor = relationship("User")

    __table_args__ = (
        Index('ix_task_events_task_id', 'task_id'),
        Index('ix_task_events_org_id', 'org_id'),
        Index('ix_task_events_processed', 'processed'),
        Index('idx_task_events_unprocessed', 'processed', 'created_at', postgresql_where=text("processed = false")),
    )