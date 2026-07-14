import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task_links import TaskLink

class TaskLinkRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        org_id: uuid.UUID,
        source_task_id: uuid.UUID,
        target_task_id: uuid.UUID,
        link_type: str
    ) -> TaskLink:
        link = TaskLink(
            org_id=org_id,
            source_task_id=source_task_id,
            target_task_id=target_task_id,
            link_type=link_type
        )
        db.add(link)
        await db.flush()
        return link

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        org_id: uuid.UUID,
        link_id: uuid.UUID
    ) -> TaskLink | None:
        result = await db.execute(
            select(TaskLink).where(
                TaskLink.org_id == org_id,
                TaskLink.id == link_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def delete(
        db: AsyncSession,
        link: TaskLink
    ) -> None:
        await db.delete(link)
        await db.flush()
