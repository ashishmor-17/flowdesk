import uuid

from sqlalchemy import String, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    full_name: Mapped[str] = mapped_column(
        String,
        nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    created_organizations = relationship("Organization", back_populates="creator")
    org_memberships = relationship("OrgMember", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    created_tasks = relationship("Task", back_populates="creator")
    assigned_tasks = relationship("TaskAssignee", foreign_keys="[TaskAssignee.user_id]", back_populates="user")
    comments = relationship("Comment", back_populates="author")
    comment_mentions = relationship("CommentMention", back_populates="mentioned_user")
    notifications = relationship("Notification", foreign_keys="[Notification.recipient_id]", back_populates="recipient",cascade="all, delete-orphan")
    sent_notifications = relationship("Notification", foreign_keys="[Notification.actor_id]", back_populates="actor")
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_users_email", "email", unique=True),
    )