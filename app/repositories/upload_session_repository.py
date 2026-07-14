import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.upload_sessions import UploadSession

class UploadSessionRepository:
    @staticmethod
    async def create_session(
        db: AsyncSession,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
        upload_id: str,
        bucket: str,
        object_key: str,
        filename: str,
        file_size: int,
        expires_at: datetime
    ) -> UploadSession:
        session = UploadSession(
            id=uuid.uuid4(),
            task_id=task_id,
            user_id=user_id,
            upload_id=upload_id,
            bucket=bucket,
            object_key=object_key,
            filename=filename,
            file_size=file_size,
            status="UPLOADING",
            parts_info=[],
            expires_at=expires_at
        )
        db.add(session)
        await db.flush()
        return session

    @staticmethod
    async def get_by_id(db: AsyncSession, session_id: uuid.UUID) -> UploadSession | None:
        return await db.get(UploadSession, session_id)

    @staticmethod
    async def update_parts_info(
        db: AsyncSession,
        session: UploadSession,
        parts_info: list
    ) -> UploadSession:
        session.parts_info = parts_info
        db.add(session)
        await db.flush()
        return session

    @staticmethod
    async def delete_session(db: AsyncSession, session: UploadSession) -> None:
        await db.delete(session)

    @staticmethod
    async def get_expired_sessions(db: AsyncSession, current_time: datetime) -> list[UploadSession]:
        result = await db.execute(
            select(UploadSession)
            .where(
                UploadSession.status == "UPLOADING",
                UploadSession.expires_at < current_time
            )
        )
        return list(result.scalars().all())
