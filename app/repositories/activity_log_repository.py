import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.activity_log import ActivityLog

class ActivityLogRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        org_id: uuid.UUID,
        actor_id: uuid.UUID | None,
        action: str,
        entity_type: str,
        entity_id: uuid.UUID,
        metadata: dict | None = None
    ) -> ActivityLog:
        activity = ActivityLog(
            org_id=org_id,
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            meta_data=metadata
        )
        db.add(activity)
        await db.flush()
        return activity

    @staticmethod
    async def list_by_task(
        db: AsyncSession,
        org_id: uuid.UUID,
        task_id: uuid.UUID
    ) -> list[ActivityLog]:
        result = await db.execute(
            select(ActivityLog)
            .where(
                ActivityLog.org_id == org_id,
                ActivityLog.entity_type == "task",
                ActivityLog.entity_id == task_id
            )
            .order_by(ActivityLog.created_at.desc())
        )
        return list(result.scalars().all())
