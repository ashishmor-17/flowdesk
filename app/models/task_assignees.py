import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, DateTime, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

class TaskAssignee(Base):
    __tablename__ = "task_assignees"

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
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=True
    )
    assignee_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="USER"
    )
    assigned_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        nullable=False
    )

    task = relationship("Task", back_populates="assignees")
    user = relationship("User", foreign_keys=[user_id], back_populates="assigned_tasks")
    assigner = relationship("User", foreign_keys=[assigned_by])
    team = relationship("Team")

Index("idx_tasks_assignee_user", TaskAssignee.user_id)
Index("idx_tasks_assignee_team", TaskAssignee.team_id)
