import uuid

from sqlalchemy import ForeignKey, String, Boolean, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

class AutomationRule(Base, TimestampMixin):
    __tablename__ = "automation_rules"

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
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True
    )
    name: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    trigger_event: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    conditions: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True
    )
    action_type: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    action_payload: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    org = relationship("Organization", back_populates="automation_rules")
    project = relationship("Project", back_populates="automation_rules")
    creator = relationship("User")

    __table_args__ = (
        Index('idx_automation_rules_org_id', 'org_id'),
        Index('idx_automation_rules_project_id', 'project_id'),
    )
