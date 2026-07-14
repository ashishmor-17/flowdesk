import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import transaction_scope
from app.models.tasks import Task
from app.repositories.time_entry_repository import TimeEntryRepository
from app.services.audit_service import AuditService

async def log_time(
    db: AsyncSession,
    org_id: uuid.UUID,
    task_id: uuid.UUID,
    user_id: uuid.UUID,
    minutes: int,
    description: str | None
):
    task = await db.get(Task, task_id)
    if not task or task.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    async with transaction_scope(db):
        entry = await TimeEntryRepository.create(
            db,
            org_id=org_id,
            task_id=task_id,
            user_id=user_id,
            minutes=minutes,
            description=description
        )
        await AuditService.create_log(
            db=db,
            org_id=org_id,
            actor_id=user_id,
            action="TIME_LOGGED",
            entity_type="task",
            entity_id=task_id,
            new_value={"minutes": minutes, "description": description}
        )
    await db.refresh(entry)
    return entry

async def list_time_entries(
    db: AsyncSession,
    org_id: uuid.UUID,
    task_id: uuid.UUID
):
    task = await db.get(Task, task_id)
    if not task or task.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    return await TimeEntryRepository.list_by_task(db, task_id)
