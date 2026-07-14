import uuid
import os
import mimetypes
import magic
import zipfile
from io import BytesIO
from pypdf import PdfReader
from PIL import Image
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.core.storage import get_storage_provider
from app.core.database import transaction_scope
from app.repositories.upload_session_repository import UploadSessionRepository
from app.repositories.attachment_repository import AttachmentRepository
from app.services import task_service
from app.models.upload_sessions import UploadSession
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

def validate_file_content(content: bytes, filename: str) -> str:
    try:
        mime = magic.from_buffer(content, mime=True)
    except Exception:
        mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == "pdf" or mime == "application/pdf":
        if mime != "application/pdf":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_FILE_TYPE",
                    "message": f"File signature indicates MIME type '{mime}', expected 'application/pdf'."
                }
            )
        try:
            reader = PdfReader(BytesIO(content))
            _ = len(reader.pages)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "CORRUPTED_FILE",
                    "message": f"Invalid or corrupted PDF file structure: {str(e)}"
                }
            )

    elif ext == "png" or mime == "image/png":
        if mime != "image/png":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_FILE_TYPE",
                    "message": f"File signature indicates MIME type '{mime}', expected 'image/png'."
                }
            )
        try:
            img = Image.open(BytesIO(content))
            img.verify()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "CORRUPTED_FILE",
                    "message": f"Invalid or corrupted PNG file structure: {str(e)}"
                }
            )

    elif ext in ["jpg", "jpeg"] or mime == "image/jpeg":
        if mime != "image/jpeg":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_FILE_TYPE",
                    "message": f"File signature indicates MIME type '{mime}', expected 'image/jpeg'."
                }
            )
        try:
            img = Image.open(BytesIO(content))
            img.verify()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "CORRUPTED_FILE",
                    "message": f"Invalid or corrupted JPEG/JPG file structure: {str(e)}"
                }
            )

    elif ext == "zip" or mime in ["application/zip", "application/x-zip-compressed"]:
        if mime not in ["application/zip", "application/x-zip-compressed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_FILE_TYPE",
                    "message": f"File signature indicates MIME type '{mime}', expected 'application/zip'."
                }
            )
        try:
            with zipfile.ZipFile(BytesIO(content)) as zf:
                bad_file = zf.testzip()
                if bad_file:
                    raise ValueError(f"Corrupted file in zip: {bad_file}")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "CORRUPTED_FILE",
                    "message": f"Invalid or corrupted ZIP file structure: {str(e)}"
                }
            )

    return mime

async def initiate_session(
    db: AsyncSession,
    org_id: uuid.UUID,
    task_id: uuid.UUID,
    filename: str,
    file_size: int,
    user_id: uuid.UUID
) -> UploadSession:
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
    unique_id = uuid.uuid4()
    if settings.STORAGE_BACKEND.lower() == "s3":
        bucket = settings.FILES_BUCKET
        object_key = f"attachments/{unique_id}_{filename}"
    else:
        bucket = "local"
        object_key = os.path.join(settings.STORAGE_LOCAL_DIR, f"{unique_id}_{filename}")
    upload_id = storage_provider.initiate_multipart(bucket, object_key)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    async with transaction_scope(db):
        session = await UploadSessionRepository.create_session(
            db=db,
            task_id=task.id,
            user_id=user_id,
            upload_id=upload_id,
            bucket=bucket,
            object_key=object_key,
            filename=filename,
            file_size=file_size,
            expires_at=expires_at
        )
    return session

async def upload_part(
    db: AsyncSession,
    org_id: uuid.UUID,
    task_id: uuid.UUID,
    session_id: uuid.UUID,
    part_number: int,
    content: bytes
) -> dict:
    await task_service.get_task(db, org_id, task_id)
    session = await UploadSessionRepository.get_by_id(db, session_id)
    if not session or session.task_id != task_id or session.status != "UPLOADING":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "SESSION_NOT_FOUND",
                "message": "Active upload session not found."
            }
        )
    settings = get_settings()
    other_parts_size = sum(p["size"] for p in session.parts_info if p["part_number"] != part_number)
    is_last_part = (other_parts_size + len(content)) >= session.file_size
    if not is_last_part and len(content) < settings.MIN_PART_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "PART_TOO_SMALL",
                "message": f"Part size must be at least {settings.MIN_PART_SIZE_BYTES / (1024*1024):.1f}MB."
            }
        )
    storage_provider = get_storage_provider()
    result = storage_provider.upload_part(
        bucket=session.bucket,
        object_key=session.object_key,
        upload_id=session.upload_id,
        part_number=part_number,
        content=content
    )
    parts_info = list(session.parts_info)
    parts_info = [p for p in parts_info if p["part_number"] != part_number]
    part_record = {
        "part_number": part_number,
        "size": len(content),
        "etag": result if session.bucket != "local" else None,
        "file_path": result if session.bucket == "local" else None
    }
    parts_info.append(part_record)
    async with transaction_scope(db):
        await UploadSessionRepository.update_parts_info(db, session, parts_info)
    return {"part_number": part_number, "status": "uploaded"}

async def get_session_progress(
    db: AsyncSession,
    org_id: uuid.UUID,
    task_id: uuid.UUID,
    session_id: uuid.UUID
) -> dict:
    await task_service.get_task(db, org_id, task_id)
    session = await UploadSessionRepository.get_by_id(db, session_id)
    if not session or session.task_id != task_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "SESSION_NOT_FOUND",
                "message": "Upload session not found."
            }
        )
    return {
        "id": session.id,
        "filename": session.filename,
        "file_size": session.file_size,
        "parts_uploaded": [p["part_number"] for p in session.parts_info],
        "expires_at": session.expires_at
    }

async def complete_session(
    db: AsyncSession,
    org_id: uuid.UUID,
    task_id: uuid.UUID,
    session_id: uuid.UUID,
    content_type: str = "application/octet-stream"
) -> TaskAttachment:
    await task_service.get_task(db, org_id, task_id)
    session = await UploadSessionRepository.get_by_id(db, session_id)
    if not session or session.task_id != task_id or session.status != "UPLOADING":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "SESSION_NOT_FOUND",
                "message": "Active upload session not found."
            }
        )
    uploaded_size = sum(p["size"] for p in session.parts_info)
    if uploaded_size < session.file_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INCOMPLETE_UPLOAD",
                "message": f"Upload is incomplete. Uploaded {uploaded_size} of {session.file_size} bytes."
            }
        )
    storage_provider = get_storage_provider()
    etag = storage_provider.complete_multipart(
        bucket=session.bucket,
        object_key=session.object_key,
        upload_id=session.upload_id,
        parts=session.parts_info
    )
    try:
        merged_content = storage_provider.get_file_stream(session.bucket, session.object_key)
        detected_mime = validate_file_content(merged_content, session.filename)
        content_type = detected_mime
    except Exception as e:
        storage_provider.delete_file(session.bucket, session.object_key)
        async with transaction_scope(db):
            await UploadSessionRepository.delete_session(db, session)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "VALIDATION_FAILED",
                "message": f"File content validation failed: {str(e)}"
            }
        )
    async with transaction_scope(db):
        attachment = await AttachmentRepository.create_attachment(
            db=db,
            task_id=session.task_id,
            user_id=session.user_id,
            bucket=session.bucket,
            object_key=session.object_key,
            filename=session.filename,
            content_type=content_type,
            size=uploaded_size,
            etag=etag
        )
        await UploadSessionRepository.delete_session(db, session)
    return attachment

async def abort_session(
    db: AsyncSession,
    org_id: uuid.UUID,
    task_id: uuid.UUID,
    session_id: uuid.UUID
) -> None:
    await task_service.get_task(db, org_id, task_id)
    session = await UploadSessionRepository.get_by_id(db, session_id)
    if not session or session.task_id != task_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "SESSION_NOT_FOUND",
                "message": "Upload session not found."
            }
        )
    storage_provider = get_storage_provider()
    storage_provider.abort_multipart(
        bucket=session.bucket,
        object_key=session.object_key,
        upload_id=session.upload_id,
        parts=session.parts_info
    )
    async with transaction_scope(db):
        await UploadSessionRepository.delete_session(db, session)

async def cleanup_expired_sessions(db: AsyncSession) -> int:
    current_time = datetime.now(timezone.utc)
    expired_sessions = await UploadSessionRepository.get_expired_sessions(db, current_time)
    storage_provider = get_storage_provider()
    count = 0
    for session in expired_sessions:
        try:
            storage_provider.abort_multipart(
                bucket=session.bucket,
                object_key=session.object_key,
                upload_id=session.upload_id,
                parts=session.parts_info
            )
        except Exception:
            pass
        async with transaction_scope(db):
            await UploadSessionRepository.delete_session(db, session)
        count += 1
    return count
