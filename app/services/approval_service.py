import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import transaction_scope
from app.core.enums import UserRole, NotificationType, NotificationEntityType
from app.models.tasks import Task
from app.models.org_members import OrgMember
from app.repositories.approval_repository import ApprovalRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.org_repository import OrgRepository
from app.services.notification_service import NotificationService

async def create_approval_request(
    db: AsyncSession,
    org_id: uuid.UUID,
    task_id: uuid.UUID,
    requestor_id: uuid.UUID,
    approver_id: uuid.UUID
):
    task = await TaskRepository.get_by_id(db, org_id, task_id)
    if not task or task.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    approver_member = await OrgRepository.get_member(db, org_id, approver_id)
    if not approver_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Approver is not a member of this organization"
        )

    async with transaction_scope(db):
        approval = await ApprovalRepository.create(
            db,
            org_id=org_id,
            task_id=task_id,
            requestor_id=requestor_id,
            approver_id=approver_id
        )
    await db.refresh(approval)
    
    NotificationService.create_notification(
        org_id=org_id,
        recipient_id=approver_id,
        type=NotificationType.APPROVAL_REQUESTED,
        actor_id=requestor_id,
        entity_type=NotificationEntityType.TASK,
        entity_id=task_id,
        payload={
            "message": f"Approval requested for task: {task.title}",
            "task_id": str(task_id),
            "approval_id": str(approval.id)
        }
    )
    
    return approval

async def decide_approval_request(
    db: AsyncSession,
    org_id: uuid.UUID,
    task_id: uuid.UUID,
    approval_id: uuid.UUID,
    decider_id: uuid.UUID,
    decider_role: str,
    status_choice: str,
    comment: str | None
):
    if decider_role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FORBIDDEN",
                "message": "Only organization Admin and Owner can approve or reject approval requests."
            }
        )

    if status_choice not in ["approved", "rejected"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Status must be 'approved' or 'rejected'"
        )

    task = await TaskRepository.get_by_id(db, org_id, task_id)
    if not task or task.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    approval = await ApprovalRepository.get_by_id_and_task(db, task_id, approval_id)
    if not approval or approval.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found"
        )

    async with transaction_scope(db):
        approval.status = status_choice
        approval.comment = comment
        await db.flush()
    await db.refresh(approval)

    NotificationService.create_notification(
        org_id=org_id,
        recipient_id=approval.requestor_id,
        type=NotificationType.APPROVAL_DECIDED,
        actor_id=decider_id,
        entity_type=NotificationEntityType.TASK,
        entity_id=task_id,
        payload={
            "message": f"Approval request was {status_choice} for task: {task.title}",
            "task_id": str(task_id),
            "approval_id": str(approval.id),
            "status": status_choice,
            "comment": comment
        }
    )

    return approval
