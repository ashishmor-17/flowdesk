import uuid
from sqlalchemy import String, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

class WorkflowRule(Base):
    __tablename__ = "workflow_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False
    )
    from_status: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    to_status: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint("project_id", "from_status", "to_status", name="uq_workflow_rules_transition"),
        Index("ix_workflow_rules_project_id", "project_id"),
        Index("ix_workflow_rules_org_id", "org_id"),
    )
