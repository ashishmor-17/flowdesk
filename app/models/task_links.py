import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

class TaskLink(Base, TimestampMixin):
    __tablename__ = "task_links"

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
    source_task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False
    )
    target_task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False
    )
    link_type: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    source_task = relationship("Task", foreign_keys=[source_task_id], back_populates="outbound_links")
    target_task = relationship("Task", foreign_keys=[target_task_id], back_populates="inbound_links")
