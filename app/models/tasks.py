import uuid
from datetime import date, datetime

from sqlalchemy import String, Date, Integer, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, SoftDeleteMixin
from app.core.enums import TaskStatus, TaskPriority


class Task(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id"),
        nullable=False,
        index=True
    )
    title: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    status: Mapped[TaskStatus] = mapped_column(
        String,
        nullable=False,
        default=TaskStatus.TODO,
        index=True
    )
    priority: Mapped[TaskPriority] = mapped_column(
        String,
        nullable=False,
        default=TaskPriority.MEDIUM,
        index=True
    )
    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1
    )

    project = relationship("Project", back_populates="tasks")
    creator = relationship("User", back_populates="created_tasks")
    assignees = relationship("TaskAssignee", back_populates="task", cascade="all, delete-orphan")
    labels = relationship("TaskLabel", back_populates="task", cascade="all, delete-orphan")

Index(
    "idx_tasks_project_id", 
    Task.project_id, 
    postgresql_where=Task.deleted_at.is_(None)
)
Index(
    "idx_tasks_org_status", 
    Task.org_id, 
    Task.status, 
    postgresql_where=Task.deleted_at.is_(None)
)
Index(
    "idx_tasks_due_date", 
    Task.due_date, 
    postgresql_where=(Task.deleted_at.is_(None)) & (Task.status != 'done')
)