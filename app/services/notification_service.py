import uuid
import base64
from datetime import datetime
from sqlalchemy import select, update, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.notifications import Notification
from app.core.redis import redis_client
from app.core.database import transaction_scope

class NotificationService:
    @staticmethod
    def create_notification(
        org_id: uuid.UUID,
        recipient_id: uuid.UUID,
        type: str,
        actor_id: uuid.UUID | None,
        entity_type: str | None,
        entity_id: uuid.UUID | None,
        payload: dict
    ) -> None:
        

        from app.workers.tasks import send_notification
        send_notification.delay(
            org_id=str(org_id),
            recipient_id=str(recipient_id),
            type=type,
            actor_id=str(actor_id) if actor_id else None,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            payload=payload
        )

    @staticmethod
    async def get_unread_count(db: AsyncSession, user_id: uuid.UUID) -> int:
        redis_key = f"user:{user_id}:unread_count"
        val = await redis_client.get(redis_key)
        if val is not None:
            return int(val)
        
        
        count = await db.scalar(
            select(func.count(Notification.id))
            .where(
                Notification.recipient_id == user_id,
                Notification.is_read == False
            )
        )
        
        await redis_client.set(redis_key, count)
        return count

    @staticmethod
    async def list_notifications(
        db: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 20,
        cursor: str | None = None
    ) -> tuple[list[Notification], str | None]:
        
        query = (
            select(Notification)
            .where(Notification.recipient_id == user_id)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .limit(limit + 1)
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
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid cursor format"
                )

        result = await db.execute(query)
        notifications = list(result.scalars().all())

        has_next = len(notifications) > limit
        next_cursor = None
        if has_next:
            notifications = notifications[:limit]
            last_item = notifications[-1]
            cursor_data = f"{last_item.created_at.isoformat()}_{last_item.id}"
            next_cursor = base64.b64encode(cursor_data.encode()).decode()

        return notifications, next_cursor

    @staticmethod
    async def mark_as_read(db: AsyncSession, user_id: uuid.UUID, notification_id: uuid.UUID) -> Notification:
        async with transaction_scope(db):
            notification = await db.scalar(
                select(Notification)
                .where(
                    Notification.id == notification_id,
                    Notification.recipient_id == user_id
                )
            )
            if not notification:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Notification not found"
                )
            
            if not notification.is_read:
                notification.is_read = True
                await db.flush()
                
                redis_key = f"user:{user_id}:unread_count"
                count = await redis_client.decr(redis_key)
                if count < 0:
                    await redis_client.set(redis_key, 0)
                    
            return notification

    @staticmethod
    async def mark_all_as_read(db: AsyncSession, user_id: uuid.UUID) -> None:
        async with transaction_scope(db):
            await db.execute(
                update(Notification)
                .where(
                    Notification.recipient_id == user_id,
                    Notification.is_read == False
                )
                .values(is_read=True)
            )
            
            redis_key = f"user:{user_id}:unread_count"
            await redis_client.set(redis_key, 0)
