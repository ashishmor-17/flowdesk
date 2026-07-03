import asyncio
import uuid
import logging
from celery.utils.log import get_task_logger

from app.workers.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.core.redis import redis_client
from app.models.notifications import Notification
from app.models.users import User

logger = get_task_logger(__name__)


@celery_app.task(name="send_test_notification")
def send_test_notification(message: str) -> str:
    logger.info(f"Received smoke test message: {message}")
    
    # Graceful failure handling test
    if message == "fail":
        raise ValueError("Simulated task failure for verification!")

    with open("celery_smoke_test.log", "a") as f:
        f.write(f"Smoke test message received: {message}\n")

    return f"Processed: {message}"


@celery_app.task(name="send_notification")
def send_notification(
    org_id: str,
    recipient_id: str,
    type: str,
    actor_id: str | None,
    entity_type: str | None,
    entity_id: str | None,
    payload: dict
) -> str:
    logger.info(f"Processing notification type={type} for recipient={recipient_id}")
    
    async def _async_save():
        try:
            o_id = uuid.UUID(org_id)
            r_id = uuid.UUID(recipient_id)
            a_id = uuid.UUID(actor_id) if actor_id else None
            e_id = uuid.UUID(entity_id) if entity_id else None

            async with AsyncSessionLocal() as db:
                notification = Notification(
                    org_id=o_id,
                    recipient_id=r_id,
                    actor_id=a_id,
                    type=type,
                    entity_type=entity_type,
                    entity_id=e_id,
                    payload=payload,
                    is_read=False
                )
                db.add(notification)
                await db.commit()

                receipent = await db.get(User, r_id)
                if receipent and receipent.is_active:
                    redis_key = f"user:{recipient_id}:unread_count"
                    await redis_client.incr(redis_key)
                    logger.info(f"Notification saved to DB and Redis counter incremented for user {recipient_id}")
                else:
                    logger.info(f"Notification saved to DB but Redis count skipped for deactivated/missing user {recipient_id}")
        finally:
            from app.core.database import engine
            await engine.dispose()
            await redis_client.close()
                
    asyncio.run(_async_save())
    return f"Notification {type} sent to {recipient_id}"