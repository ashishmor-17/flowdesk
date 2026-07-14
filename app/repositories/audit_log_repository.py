import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog

class AuditLogRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        org_id: uuid.UUID,
        actor_id: uuid.UUID | None,
        action: str,
        entity_type: str,
        entity_id: uuid.UUID,
        old_value: dict | None = None,
        new_value: dict | None = None
    ) -> AuditLog:
        audit = AuditLog(
            org_id=org_id,
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value
        )
        db.add(audit)
        await db.flush()
        return audit

    @staticmethod
    async def list_by_org(
        db: AsyncSession,
        org_id: uuid.UUID
    ) -> list[AuditLog]:
        result = await db.execute(
            select(AuditLog)
            .where(AuditLog.org_id == org_id)
            .order_by(AuditLog.created_at.desc())
        )
        return list(result.scalars().all())
