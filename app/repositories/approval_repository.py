import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.approval_requests import ApprovalRequest

class ApprovalRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        org_id: uuid.UUID,
        task_id: uuid.UUID,
        requestor_id: uuid.UUID,
        approver_id: uuid.UUID
    ) -> ApprovalRequest:
        approval = ApprovalRequest(
            org_id=org_id,
            task_id=task_id,
            requestor_id=requestor_id,
            approver_id=approver_id,
            status="pending"
        )
        db.add(approval)
        await db.flush()
        return approval

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        approval_id: uuid.UUID
    ) -> ApprovalRequest | None:
        return await db.get(ApprovalRequest, approval_id)

    @staticmethod
    async def get_by_id_and_task(
        db: AsyncSession,
        task_id: uuid.UUID,
        approval_id: uuid.UUID
    ) -> ApprovalRequest | None:
        return await db.scalar(
            select(ApprovalRequest).where(
                ApprovalRequest.id == approval_id,
                ApprovalRequest.task_id == task_id
            )
        )
