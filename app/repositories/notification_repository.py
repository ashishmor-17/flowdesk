import uuid
import base64
from datetime import datetime
from sqlalchemy import select, and_, or_, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notifications import Notification

class NotificationRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        org_id: uuid.UUID,
        recipient_id: uuid.UUID,
        type: str,
        actor_id: uuid.UUID | None = None,
        entity_type: str | None = None,
        entity_id: uuid.UUID | None = None,
        payload: dict
    ) -> Notification:
        notification = Notification(
            org_id=org_id,
            recipient_id=recipient_id,
            type=type,
            actor_id=actor_id,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload
        )
        db.add(notification)
        await db.flush()
        return notification

    @staticmethod
    async def get_unread_count(db: AsyncSession, recipient_id: uuid.UUID) -> int:
        return await db.scalar(
            select(func.count(Notification.id))
            .where(
                Notification.recipient_id == recipient_id,
                Notification.is_read == False
            )
        )

    @staticmethod
    async def list_notifications(
        db: AsyncSession,
        recipient_id: uuid.UUID,
        limit: int = 20,
        cursor: str | None = None
    ) -> tuple[list[Notification], str | None]:
        query = (
            select(Notification)
            .where(Notification.recipient_id == recipient_id)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
        )

        if cursor:
            try:
                decoded = base64.b64decode(cursor.encode()).decode()
                cursor_time_str, cursor_id_str = decoded.split("_")
                cursor_time = datetime.fromisoformat(cursor_time_str)
                cursor_id = uuid.UUID(cursor_id_str)

                query = query.where(
                    or_(
                        Notification.created_at < cursor_time,
                        and_(
                            Notification.created_at == cursor_time,
                            Notification.id < cursor_id
                        )
                    )
                )
            except Exception:
                raise ValueError("Invalid pagination cursor")

        result = await db.execute(query.limit(limit + 1))
        notifications = list(result.scalars().all())

        next_cursor = None
        if len(notifications) > limit:
            notifications = notifications[:limit]
            last_notification = notifications[-1]
            cursor_str = f"{last_notification.created_at.isoformat()}_{last_notification.id}"
            next_cursor = base64.b64encode(cursor_str.encode()).decode()

        return notifications, next_cursor

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        recipient_id: uuid.UUID,
        notification_id: uuid.UUID
    ) -> Notification | None:
        return await db.scalar(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.recipient_id == recipient_id
            )
        )

    @staticmethod
    async def mark_all_as_read(db: AsyncSession, recipient_id: uuid.UUID) -> None:
        await db.execute(
            update(Notification)
            .where(Notification.recipient_id == recipient_id, Notification.is_read == False)
            .values(is_read=True, updated_at=datetime.utcnow())
        )
