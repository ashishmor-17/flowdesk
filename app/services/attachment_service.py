import uuid
import mimetypes
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import transaction_scope
from app.core.config import get_settings
from app.core.storage import get_storage_provider
from app.models.task_attachments import TaskAttachment
from app.repositories.attachment_repository import AttachmentRepository
from app.services import task_service
from app.services.upload_session_service import validate_file_extension, validate_file_content

async def create_attachment(
    db: AsyncSession,
    org_id: uuid.UUID,
    task_id: uuid.UUID,
    filename: str,
    file_content: bytes,
    uploaded_by: uuid.UUID,
    content_type: str = "application/octet-stream"
) -> TaskAttachment:
    validate_file_extension(filename)
    settings = get_settings()
    if len(file_content) > settings.MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "code": "FILE_TOO_LARGE",
                "message": f"File size exceeds the maximum limit of {settings.MAX_FILE_SIZE_BYTES / (1024*1024):.0f}MB."
            }
        )
    content_type = validate_file_content(file_content, filename)
    task = await task_service.get_task(db, org_id, task_id)
    storage_provider = get_storage_provider()
    storage_filename = f"{uuid.uuid4()}_{filename}"
    bucket, object_key = storage_provider.upload_file(file_content, storage_filename)
    async with transaction_scope(db):
        attachment = await AttachmentRepository.create_attachment(
            db=db,
            task_id=task.id,
            user_id=uploaded_by,
            bucket=bucket,
            object_key=object_key,
            filename=filename,
            content_type=content_type,
            size=len(file_content)
        )
    return attachment

async def list_attachments(
    db: AsyncSession,
    org_id: uuid.UUID,
    task_id: uuid.UUID
) -> list[TaskAttachment]:
    await task_service.get_task(db, org_id, task_id)
    return await AttachmentRepository.list_by_task(db, task_id)

async def get_attachment_file(
    db: AsyncSession,
    org_id: uuid.UUID,
    task_id: uuid.UUID,
    attachment_id: uuid.UUID
) -> tuple[bytes, str]:
    await task_service.get_task(db, org_id, task_id)
    attachment = await AttachmentRepository.get_by_id(db, attachment_id)
    if not attachment or attachment.task_id != task_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "ATTACHMENT_NOT_FOUND",
                "message": "Attachment not found or does not belong to the task."
            }
        )
    storage_provider = get_storage_provider()
    try:
        content = storage_provider.get_file_stream(attachment.bucket, attachment.object_key)
        return content, attachment.filename
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "STORAGE_ERROR",
                "message": f"Failed to retrieve file from storage: {str(e)}"
            }
        )

async def delete_attachment(
    db: AsyncSession,
    org_id: uuid.UUID,
    task_id: uuid.UUID,
    attachment_id: uuid.UUID,
    user_id: uuid.UUID,
    user_role: str
) -> None:
    await task_service.get_task(db, org_id, task_id)
    attachment = await AttachmentRepository.get_by_id(db, attachment_id)
    if not attachment or attachment.task_id != task_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "ATTACHMENT_NOT_FOUND",
                "message": "Attachment not found or does not belong to the task."
            }
        )
    is_uploader = attachment.user_id == user_id
    is_privileged = user_role.lower() in ["owner", "admin"]
    if not is_uploader and not is_privileged:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FORBIDDEN",
                "message": "You do not have permission to delete this attachment."
            }
        )
    storage_provider = get_storage_provider()
    storage_provider.delete_file(attachment.bucket, attachment.object_key)
    async with transaction_scope(db):
        await AttachmentRepository.delete(db, attachment)
