import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task_attachments import TaskAttachment

class AttachmentRepository:
    @staticmethod
    async def create_attachment(
        db: AsyncSession,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
        bucket: str,
        object_key: str,
        filename: str,
        content_type: str,
        size: int,
        etag: str | None = None
    ) -> TaskAttachment:
        attachment = TaskAttachment(
            id=uuid.uuid4(),
            task_id=task_id,
            user_id=user_id,
            bucket=bucket,
            object_key=object_key,
            filename=filename,
            content_type=content_type,
            size=size,
            etag=etag
        )
        db.add(attachment)
        await db.flush()
        return attachment

    @staticmethod
    async def get_by_id(db: AsyncSession, attachment_id: uuid.UUID) -> TaskAttachment | None:
        return await db.get(TaskAttachment, attachment_id)

    @staticmethod
    async def list_by_task(db: AsyncSession, task_id: uuid.UUID) -> list[TaskAttachment]:
        result = await db.execute(
            select(TaskAttachment)
            .where(TaskAttachment.task_id == task_id)
            .order_by(TaskAttachment.created_at.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def delete(db: AsyncSession, attachment: TaskAttachment) -> None:
        await db.delete(attachment)
