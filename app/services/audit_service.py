import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.activity_log_repository import ActivityLogRepository
from app.models.audit_log import AuditLog
from app.models.activity_log import ActivityLog

class AuditService:
    @staticmethod
    async def create_log(
        db: AsyncSession,
        *,
        org_id: uuid.UUID,
        actor_id: uuid.UUID | None,
        action: str,
        entity_type: str,
        entity_id: uuid.UUID,
        old_value: dict | None = None,
        new_value: dict | None = None,
        metadata: dict | None = None
    ) -> None:
        await AuditLogRepository.create(
            db=db,
            org_id=org_id,
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value
        )
        
        act_metadata = metadata if metadata is not None else (new_value or {})
        await ActivityLogRepository.create(
            db=db,
            org_id=org_id,
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata=act_metadata
        )

    @staticmethod
    async def list_org_audit_logs(
        db: AsyncSession,
        org_id: uuid.UUID
    ) -> list[AuditLog]:
        return await AuditLogRepository.list_by_org(db, org_id)

    @staticmethod
    async def list_task_activity_logs(
        db: AsyncSession,
        org_id: uuid.UUID,
        task_id: uuid.UUID
    ) -> list[ActivityLog]:
        return await ActivityLogRepository.list_by_task(db, org_id, task_id)
