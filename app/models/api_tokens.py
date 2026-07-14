import uuid
from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base, TimestampMixin

class APIToken(Base, TimestampMixin):
    __tablename__ = "api_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    token_hash: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False
    )
    name: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    expires_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    user = relationship("User")
