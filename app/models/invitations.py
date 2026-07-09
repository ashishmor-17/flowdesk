import uuid
from datetime import datetime, timedelta

from sqlalchemy import String, ForeignKey, DateTime, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.core.enums import UserRole, InvitationStatus


class Invitation(Base, TimestampMixin):
    __tablename__ = "invitations"

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
    invited_email: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    invited_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    token: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False
    )
    role: Mapped[UserRole] = mapped_column(
        String,
        nullable=False
    )
    status: Mapped[InvitationStatus] = mapped_column(
        String,
        nullable=False,
        default=InvitationStatus.PENDING
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.utcnow() + timedelta(days=7)
    )

    organization = relationship("Organization")
    inviter = relationship("User")

    __table_args__ = (
        Index("ix_invitations_token", "token", unique=True),
    )