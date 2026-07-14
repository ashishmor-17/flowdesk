import uuid
from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

class UserProfile(Base, TimestampMixin):
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    first_name: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    last_name: Mapped[str] = mapped_column(
        String,
        nullable=True
    )
    preferences: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        server_default="{}",
        nullable=False
    )

    user = relationship("User", back_populates="profile")
