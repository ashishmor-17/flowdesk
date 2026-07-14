import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.core.storage import get_storage_provider
from app.core.database import transaction_scope
from app.repositories.multipart_repository import MultipartRepository
from app.repositories.attachment_repository import AttachmentRepository
from app.services import task_service
from app.models.multipart_uploads import MultipartUpload
from app.models.task_attachments import TaskAttachment

def validate_file_extension(filename: str) -> None:
    settings = get_settings()
    allowed = [ext.strip().lower().lstrip(".") for ext in settings.ALLOWED_EXTENSIONS.split(",")]
    if "." not in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_FILE_EXTENSION",
                "message": "File has no extension."
            }
        )
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_FILE_EXTENSION",
                "message": f"Extension .{ext} is not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}"
            }
        )

async def initiate_upload(
    db: AsyncSession,
    org_id: uuid.UUID,
    task_id: uuid.UUID,
    filename: str,
    file_size: int,
    uploaded_by: uuid.UUID
) -> MultipartUpload:

    validate_file_extension(filename)

    task = await task_service.get_task(db, org_id, task_id)

    settings = get_settings()
    if file_size > settings.MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "code": "FILE_TOO_LARGE",
                "message": f"File size exceeds the maximum limit of {settings.MAX_FILE_SIZE_BYTES / (1024*1024):.0f}MB."
            }
        )

    storage_provider = get_storage_provider()
    upload_id = uuid.uuid4()
    storage_filename = f"{upload_id}_{filename}"
    s3_upload_id = None
    if settings.STORAGE_BACKEND.lower() == "s3":
        s3_upload_id = storage_provider.initiate_multipart(storage_filename)

    async with transaction_scope(db):
        upload = MultipartUpload(
            id=upload_id,
            task_id=task.id,
            filename=filename,
            file_size=file_size,
            uploaded_by=uploaded_by,
            storage_backend=settings.STORAGE_BACKEND.lower(),
            s3_upload_id=s3_upload_id,
            parts_info=[]
        )
        db.add(upload)
    return upload

async def upload_part(
    db: AsyncSession,
    org_id: uuid.UUID,
    task_id: uuid.UUID,
    upload_id: uuid.UUID,
    part_number: int,
    content: bytes
) -> dict:
    
    await task_service.get_task(db, org_id, task_id)

    upload = await MultipartRepository.get_by_id(db, upload_id)
    if not upload or upload.task_id != task_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "UPLOAD_NOT_FOUND",
                "message": "Multipart upload session not found."
            }
        )

    settings = get_settings()
    other_parts_size = sum(p["size"] for p in upload.parts_info if p["part_number"] != part_number)
    is_last_part = (other_parts_size + len(content)) >= upload.file_size

    if not is_last_part and len(content) < settings.MIN_PART_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "PART_TOO_SMALL",
                "message": f"Part size must be at least {settings.MIN_PART_SIZE_BYTES / (1024*1024):.1f}MB."
            }
        )

    storage_provider = get_storage_provider()
    storage_filename = f"{upload.id}_{upload.filename}"
    upload_identifier = upload.s3_upload_id if upload.storage_backend == "s3" else str(upload.id)
    
    result = storage_provider.upload_part(
        filename=storage_filename,
        upload_id=upload_identifier,
        part_number=part_number,
        content=content
    )

    parts_info = list(upload.parts_info)
    parts_info = [p for p in parts_info if p["part_number"] != part_number]
    
    part_record = {
        "part_number": part_number,
        "size": len(content),
        "etag": result if upload.storage_backend == "s3" else None,
        "file_path": result if upload.storage_backend != "s3" else None
    }
    parts_info.append(part_record)

    async with transaction_scope(db):
        await MultipartRepository.update_parts_info(db, upload, parts_info)

    return {"part_number": part_number, "status": "uploaded"}

async def get_upload_progress(
    db: AsyncSession,
    org_id: uuid.UUID,
    task_id: uuid.UUID,
    upload_id: uuid.UUID
) -> dict:
    
    await task_service.get_task(db, org_id, task_id)
    upload = await MultipartRepository.get_by_id(db, upload_id)
    if not upload or upload.task_id != task_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "UPLOAD_NOT_FOUND",
                "message": "Multipart upload session not found."
            }
        )
    return {
        "upload_id": upload.id,
        "filename": upload.filename,
        "file_size": upload.file_size,
        "parts_uploaded": [p["part_number"] for p in upload.parts_info],
        "created_at": upload.created_at
    }

async def complete_upload(
    db: AsyncSession,
    org_id: uuid.UUID,
    task_id: uuid.UUID,
    upload_id: uuid.UUID
) -> TaskAttachment:
    
    await task_service.get_task(db, org_id, task_id)
    upload = await MultipartRepository.get_by_id(db, upload_id)
    if not upload or upload.task_id != task_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "UPLOAD_NOT_FOUND",
                "message": "Multipart upload session not found."
            }
        )

    uploaded_size = sum(p["size"] for p in upload.parts_info)
    if uploaded_size < upload.file_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INCOMPLETE_UPLOAD",
                "message": f"Upload is incomplete. Uploaded {uploaded_size} of {upload.file_size} bytes."
            }
        )

    storage_provider = get_storage_provider()
    storage_filename = f"{upload.id}_{upload.filename}"
    upload_identifier = upload.s3_upload_id if upload.storage_backend == "s3" else str(upload.id)
    
    storage_path = storage_provider.complete_multipart(
        filename=storage_filename,
        upload_id=upload_identifier,
        parts=upload.parts_info
    )

    async with transaction_scope(db):
        attachment = await AttachmentRepository.create_attachment(
            db=db,
            task_id=upload.task_id,
            filename=upload.filename,
            file_size=uploaded_size,
            url=storage_path,
            uploaded_by=upload.uploaded_by
        )
        await MultipartRepository.delete_upload(db, upload)

    return attachment

async def abort_upload(
    db: AsyncSession,
    org_id: uuid.UUID,
    task_id: uuid.UUID,
    upload_id: uuid.UUID
) -> None:
    
    await task_service.get_task(db, org_id, task_id)
    upload = await MultipartRepository.get_by_id(db, upload_id)
    if not upload or upload.task_id != task_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "UPLOAD_NOT_FOUND",
                "message": "Multipart upload session not found."
            }
        )

    storage_provider = get_storage_provider()
    storage_filename = f"{upload.id}_{upload.filename}"
    upload_identifier = upload.s3_upload_id if upload.storage_backend == "s3" else str(upload.id)
    
    storage_provider.abort_multipart(
        filename=storage_filename,
        upload_id=upload_identifier,
        parts=upload.parts_info
    )

    async with transaction_scope(db):
        await MultipartRepository.delete_upload(db, upload)
