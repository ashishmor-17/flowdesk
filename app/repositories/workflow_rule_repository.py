import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.workflow_rules import WorkflowRule

class WorkflowRuleRepository:
    @staticmethod
    async def list_by_project(db: AsyncSession, project_id: uuid.UUID) -> list[WorkflowRule]:
        result = await db.scalars(
            select(WorkflowRule).where(WorkflowRule.project_id == project_id)
        )
        return list(result.all())

    @staticmethod
    async def get_by_transition(
        db: AsyncSession,
        project_id: uuid.UUID,
        from_status: str,
        to_status: str
    ) -> WorkflowRule | None:
        return await db.scalar(
            select(WorkflowRule).where(
                WorkflowRule.project_id == project_id,
                WorkflowRule.from_status == from_status,
                WorkflowRule.to_status == to_status
            )
        )

    @staticmethod
    async def create(
        db: AsyncSession,
        project_id: uuid.UUID,
        org_id: uuid.UUID,
        from_status: str,
        to_status: str
    ) -> WorkflowRule:
        rule = WorkflowRule(
            project_id=project_id,
            org_id=org_id,
            from_status=from_status,
            to_status=to_status
        )
        db.add(rule)
        await db.flush()
        return rule
