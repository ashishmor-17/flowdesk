import uuid
from datetime import datetime
from sqlalchemy import DateTime, String, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

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
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    action: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    entity_type: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False
    )
    old_value: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True
    )
    new_value: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    __table_args__ = (
        Index("ix_audit_logs_org_created", "org_id", "created_at"),
        Index("ix_audit_logs_entity_created", "entity_type", "entity_id", "created_at"),
    )
