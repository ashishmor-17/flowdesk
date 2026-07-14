import uuid
from sqlalchemy import String, ForeignKey, Integer, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

class ProjectStatusModel(Base):
    __tablename__ = "project_statuses"

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
    name: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    color: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )
    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_project_statuses_project_name"),
        Index("ix_project_statuses_project_id", "project_id"),
        Index("ix_project_statuses_org_id", "org_id"),
    )
