import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

class TimeEntry(Base, TimestampMixin):
    __tablename__ = "time_entries"

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
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    description: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    task = relationship("Task", back_populates="time_entries")
    org = relationship("Organization")
    user = relationship("User")
