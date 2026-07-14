import uuid
from sqlalchemy import ForeignKey, String, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

class AutomationHistory(Base, TimestampMixin):
    __tablename__ = "automation_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automation_rules.id", ondelete="CASCADE"),
        nullable=False
    )
    event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("task_events.id", ondelete="SET NULL"),
        nullable=True
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=True
    )
    success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    action_type: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    rule = relationship("AutomationRule")
    event = relationship("TaskEvent")
    task = relationship("Task")
