import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.sla_policies import SLAPolicy
from app.models.sla_timers import SLATimer
from app.models.tasks import Task

class SLARepository:
    @staticmethod
    async def get_policy_by_priority(db: AsyncSession, org_id: uuid.UUID, priority: str) -> SLAPolicy | None:
        return await db.scalar(
            select(SLAPolicy).where(
                SLAPolicy.org_id == org_id,
                SLAPolicy.priority == priority
            )
        )

    @staticmethod
    async def create_policy(
        db: AsyncSession,
        *,
        org_id: uuid.UUID,
        name: str,
        priority: str,
        duration_minutes: int
    ) -> SLAPolicy:
        policy = SLAPolicy(
            org_id=org_id,
            name=name,
            priority=priority,
            duration_minutes=duration_minutes
        )
        db.add(policy)
        await db.flush()
        return policy

    @staticmethod
    async def list_policies(db: AsyncSession, org_id: uuid.UUID) -> list[SLAPolicy]:
        result = await db.scalars(
            select(SLAPolicy).where(SLAPolicy.org_id == org_id).order_by(SLAPolicy.created_at.desc())
        )
        return list(result.all())

    @staticmethod
    async def get_timer_by_task_id(db: AsyncSession, task_id: uuid.UUID) -> SLATimer | None:
        return await db.scalar(
            select(SLATimer).where(SLATimer.task_id == task_id)
        )

    @staticmethod
    async def create_timer(
        db: AsyncSession,
        *,
        task_id: uuid.UUID,
        policy_id: uuid.UUID,
        status: str,
        deadline: datetime,
        warning_at: datetime,
        warning_sent: bool = False,
        breached_sent: bool = False
    ) -> SLATimer:
        timer = SLATimer(
            task_id=task_id,
            policy_id=policy_id,
            status=status,
            deadline=deadline,
            warning_at=warning_at,
            warning_sent=warning_sent,
            breached_sent=breached_sent
        )
        db.add(timer)
        await db.flush()
        return timer

    @staticmethod
    async def list_active_timers(db: AsyncSession) -> list[SLATimer]:
        result = await db.execute(
            select(SLATimer)
            .where(SLATimer.status.in_(["active", "warning", "breached"]))
            .options(
                selectinload(SLATimer.task).selectinload(Task.assignees),
            )
        )
        return list(result.scalars().all())
