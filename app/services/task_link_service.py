import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import transaction_scope
from app.models.tasks import Task
from app.repositories.task_link_repository import TaskLinkRepository
from app.services.audit_service import AuditService

async def create_link(
    db: AsyncSession,
    org_id: uuid.UUID,
    source_task_id: uuid.UUID,
    target_task_id: uuid.UUID,
    link_type: str,
    actor_id: uuid.UUID
):
    if source_task_id == target_task_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot link a task to itself"
        )

    source_task = await db.get(Task, source_task_id)
    target_task = await db.get(Task, target_task_id)

    if not source_task or not target_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    if source_task.org_id != org_id or target_task.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot link tasks from different organizations"
        )

    async with transaction_scope(db):
        link = await TaskLinkRepository.create(
            db,
            org_id=org_id,
            source_task_id=source_task_id,
            target_task_id=target_task_id,
            link_type=link_type
        )
        await AuditService.create_log(
            db=db,
            org_id=org_id,
            actor_id=actor_id,
            action="TASK_LINKED",
            entity_type="task",
            entity_id=source_task_id,
            new_value={"target_task_id": str(target_task_id), "link_type": link_type, "direction": "outbound"}
        )
        await AuditService.create_log(
            db=db,
            org_id=org_id,
            actor_id=actor_id,
            action="TASK_LINKED",
            entity_type="task",
            entity_id=target_task_id,
            new_value={"source_task_id": str(source_task_id), "link_type": link_type, "direction": "inbound"}
        )
    await db.refresh(link)
    return link

async def delete_link(
    db: AsyncSession,
    org_id: uuid.UUID,
    source_task_id: uuid.UUID,
    link_id: uuid.UUID,
    actor_id: uuid.UUID
):
    link = await TaskLinkRepository.get_by_id(db, org_id, link_id)
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task dependency link not found"
        )

    if link.source_task_id != source_task_id and link.target_task_id != source_task_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Link does not belong to the specified task"
        )

    async with transaction_scope(db):
        await AuditService.create_log(
            db=db,
            org_id=org_id,
            actor_id=actor_id,
            action="TASK_UNLINKED",
            entity_type="task",
            entity_id=link.source_task_id,
            old_value={"target_task_id": str(link.target_task_id), "link_type": link.link_type, "direction": "outbound"}
        )
        await AuditService.create_log(
            db=db,
            org_id=org_id,
            actor_id=actor_id,
            action="TASK_UNLINKED",
            entity_type="task",
            entity_id=link.target_task_id,
            old_value={"source_task_id": str(link.source_task_id), "link_type": link.link_type, "direction": "inbound"}
        )
        await TaskLinkRepository.delete(db, link)
