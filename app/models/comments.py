import uuid
from datetime import datetime
from sqlalchemy import Text, ForeignKey, Boolean, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, SoftDeleteMixin

class Comment(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "comments"

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
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    edited_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None
    )

    task = relationship("Task", back_populates="comments")
    author = relationship("User", back_populates="comments")
    mentions = relationship("CommentMention", back_populates="comment", cascade="all, delete-orphan")

Index("idx_comments_task_id", Comment.task_id, postgresql_where=Comment.deleted_at.is_(None))

class CommentMention(Base):
    __tablename__ = "comment_mentions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        default=uuid.uuid4
    )
    comment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=False
    )
    mentioned_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )
    notified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    comment = relationship("Comment", back_populates="mentions")
    mentioned_user = relationship("User", back_populates="comment_mentions")