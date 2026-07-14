import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.multipart_uploads import MultipartUpload

class MultipartRepository:
    @staticmethod
    async def create_upload(
        db: AsyncSession,
        task_id: uuid.UUID,
        filename: str,
        file_size: int,
        uploaded_by: uuid.UUID,
        storage_backend: str,
        s3_upload_id: str | None = None
    ) -> MultipartUpload:
        upload = MultipartUpload(
            id=uuid.uuid4(),
            task_id=task_id,
            filename=filename,
            file_size=file_size,
            uploaded_by=uploaded_by,
            storage_backend=storage_backend,
            s3_upload_id=s3_upload_id,
            parts_info=[]
        )
        db.add(upload)
        await db.flush()
        return upload

    @staticmethod
    async def get_by_id(db: AsyncSession, upload_id: uuid.UUID) -> MultipartUpload | None:
        return await db.get(MultipartUpload, upload_id)

    @staticmethod
    async def update_parts_info(
        db: AsyncSession,
        upload: MultipartUpload,
        parts_info: list
    ) -> MultipartUpload:
        upload.parts_info = parts_info
        db.add(upload)
        await db.flush()
        return upload

    @staticmethod
    async def delete_upload(db: AsyncSession, upload: MultipartUpload) -> None:
        await db.delete(upload)
