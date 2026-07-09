import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.notifications import Notification
from app.core.redis import redis_client
from app.core.database import transaction_scope
from app.repositories.notification_repository import NotificationRepository

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
        
        count = await NotificationRepository.get_unread_count(db, user_id)
        await redis_client.set(redis_key, count)
        return count

    @staticmethod
    async def list_notifications(
        db: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 20,
        cursor: str | None = None
    ) -> tuple[list[Notification], str | None]:
        try:
            return await NotificationRepository.list_notifications(
                db=db,
                recipient_id=user_id,
                limit=limit,
                cursor=cursor
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    @staticmethod
    async def mark_as_read(db: AsyncSession, user_id: uuid.UUID, notification_id: uuid.UUID) -> Notification:
        async with transaction_scope(db):
            notification = await NotificationRepository.get_by_id(db, user_id, notification_id)
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
            await NotificationRepository.mark_all_as_read(db, user_id)
            
            redis_key = f"user:{user_id}:unread_count"
            await redis_client.set(redis_key, 0)
