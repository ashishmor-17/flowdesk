import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.automation_rules import AutomationRule
from app.models.automation_history import AutomationHistory

class AutomationRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        org_id: uuid.UUID,
        project_id: uuid.UUID | None,
        name: str,
        trigger_event: str,
        conditions: dict | None,
        action_type: str,
        action_payload: dict | None,
        created_by: uuid.UUID
    ) -> AutomationRule:
        rule = AutomationRule(
            org_id=org_id,
            project_id=project_id,
            name=name,
            trigger_event=trigger_event,
            conditions=conditions,
            action_type=action_type,
            action_payload=action_payload,
            created_by=created_by
        )
        db.add(rule)
        await db.flush()
        return rule

    @staticmethod
    async def list_rules(
        db: AsyncSession,
        org_id: uuid.UUID,
        project_id: uuid.UUID | None = None
    ) -> list[AutomationRule]:
        query = select(AutomationRule).where(AutomationRule.org_id == org_id)
        if project_id is not None:
            query = query.where(AutomationRule.project_id == project_id)
        result = await db.scalars(query)
        return list(result.all())

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        org_id: uuid.UUID,
        rule_id: uuid.UUID
    ) -> AutomationRule | None:
        return await db.scalar(
            select(AutomationRule).where(
                AutomationRule.id == rule_id,
                AutomationRule.org_id == org_id
            )
        )

    @staticmethod
    async def delete(db: AsyncSession, rule: AutomationRule) -> None:
        await db.delete(rule)

    @staticmethod
    async def list_history(
        db: AsyncSession,
        rule_id: uuid.UUID
    ) -> list[AutomationHistory]:
        result = await db.scalars(
            select(AutomationHistory)
            .where(AutomationHistory.rule_id == rule_id)
            .order_by(AutomationHistory.created_at.desc())
        )
        return list(result.all())
