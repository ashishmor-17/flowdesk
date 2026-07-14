import uuid
from datetime import datetime

from sqlalchemy import String, ForeignKey, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

class SLATimer(Base, TimestampMixin):
    __tablename__ = "sla_timers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    policy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sla_policies.id", ondelete="CASCADE"),
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active"
    )
    deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    warning_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    warning_sent: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )
    breached_sent: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )
    last_breached_notification_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    task = relationship("Task", back_populates="sla_timer")
    policy = relationship("SLAPolicy")
