import uuid

from sqlalchemy import String, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.core.enums import ProjectStatus


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

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
        String,
        nullable=False
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    color: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )
    status: Mapped[ProjectStatus] = mapped_column(
        String,
        nullable=False,
        default=ProjectStatus.ACTIVE
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    organization = relationship("Organization")
    creator = relationship("User")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan", passive_deletes=True)
    automation_rules = relationship("AutomationRule", back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_projects_org_id", "org_id"),
        Index("ix_projects_status", "status"),
        Index("idx_projects_org_id", "org_id"),
        Index("idx_projects_org_status", "org_id", "status"),
    )