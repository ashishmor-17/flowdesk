import uuid
from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.core.enums import TaskPriority

class SLAPolicy(Base, TimestampMixin):
    __tablename__ = "sla_policies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    priority: Mapped[TaskPriority] = mapped_column(
        String,
        nullable=False
    )
    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint("org_id", "priority", name="uq_sla_policies_org_priority"),
    )
