import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.time_entries import TimeEntry

class TimeEntryRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        org_id: uuid.UUID,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
        minutes: int,
        description: str | None
    ) -> TimeEntry:
        entry = TimeEntry(
            org_id=org_id,
            task_id=task_id,
            user_id=user_id,
            minutes=minutes,
            description=description
        )
        db.add(entry)
        await db.flush()
        return entry

    @staticmethod
    async def list_by_task(
        db: AsyncSession,
        task_id: uuid.UUID
    ) -> list[TimeEntry]:
        result = await db.execute(
            select(TimeEntry)
            .where(TimeEntry.task_id == task_id)
            .order_by(TimeEntry.created_at.asc())
        )
        return list(result.scalars().all())
