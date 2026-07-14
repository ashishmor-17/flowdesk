import uuid
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task_watchers import TaskWatcher

class TaskWatcherRepository:
    @staticmethod
    async def get(db: AsyncSession, task_id: uuid.UUID, user_id: uuid.UUID) -> TaskWatcher | None:
        return await db.scalar(
            select(TaskWatcher).where(
                TaskWatcher.task_id == task_id,
                TaskWatcher.user_id == user_id
            )
        )

    @staticmethod
    async def list_by_task(db: AsyncSession, task_id: uuid.UUID) -> list[TaskWatcher]:
        result = await db.scalars(
            select(TaskWatcher).where(TaskWatcher.task_id == task_id)
        )
        return list(result.all())

    @staticmethod
    async def create(
        db: AsyncSession,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
        org_id: uuid.UUID
    ) -> TaskWatcher:
        watcher = TaskWatcher(
            task_id=task_id,
            user_id=user_id,
            org_id=org_id
        )
        db.add(watcher)
        await db.flush()
        return watcher

    @staticmethod
    async def delete(db: AsyncSession, watcher: TaskWatcher) -> None:
        await db.delete(watcher)
        await db.flush()
