import uuid
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sla_policies import SLAPolicy
from app.models.sla_timers import SLATimer
from app.models.tasks import Task
from app.schemas.sla import SLAPolicyCreate
from app.core.database import transaction_scope
from app.services.notification_service import NotificationService
from app.core.enums import NotificationType, NotificationEntityType
from app.repositories.sla_repository import SLARepository
from app.repositories.task_watcher_repository import TaskWatcherRepository

async def create_sla_policy(
    db: AsyncSession,
    org_id: uuid.UUID,
    payload: SLAPolicyCreate
) -> SLAPolicy:
    async with transaction_scope(db):
        existing = await SLARepository.get_policy_by_priority(db, org_id, payload.priority)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "SLA_POLICY_EXISTS",
                    "message": f"SLA Policy for priority '{payload.priority}' already exists."
                }
            )

        return await SLARepository.create_policy(
            db,
            org_id=org_id,
            name=payload.name,
            priority=payload.priority,
            duration_minutes=payload.duration_minutes
        )

async def list_sla_policies(
    db: AsyncSession,
    org_id: uuid.UUID
) -> list[SLAPolicy]:
    return await SLARepository.list_policies(db, org_id)

async def check_and_create_sla_timer(
    db: AsyncSession,
    org_id: uuid.UUID,
    task: Task
) -> SLATimer | None:
    policy = await SLARepository.get_policy_by_priority(db, org_id, task.priority)
    if not policy:
        return None

    created_at = task.created_at or datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    deadline = created_at + timedelta(minutes=policy.duration_minutes)
    warning_at = created_at + timedelta(minutes=policy.duration_minutes * 0.75)

    status_lower = task.status.lower() if task.status else ""
    timer_status = "completed" if status_lower in ["done", "completed"] else "active"

    return await SLARepository.create_timer(
        db,
        task_id=task.id,
        policy_id=policy.id,
        status=timer_status,
        deadline=deadline,
        warning_at=warning_at
    )

async def update_sla_timer_status(
    db: AsyncSession,
    task: Task
) -> None:
    timer = await SLARepository.get_timer_by_task_id(db, task.id)
    if not timer:
        return

    status_lower = task.status.lower() if task.status else ""
    if status_lower in ["done", "completed"]:
        timer.status = "completed"
    else:
        now = datetime.now(timezone.utc)
        if now >= timer.deadline:
            timer.status = "breached"
        elif now >= timer.warning_at:
            timer.status = "warning"
        else:
            timer.status = "active"
    await db.flush()


async def scan_and_evaluate_sla_timers(db: AsyncSession) -> int:
    timers = await SLARepository.list_active_timers(db)
    now = datetime.now(timezone.utc)
    
    updated_count = 0
    for timer in timers:
        if not timer.task or timer.task.deleted_at is not None:
            timer.status = "completed"
            updated_count += 1
            continue

        task_status_lower = timer.task.status.lower() if timer.task.status else ""
        if task_status_lower in ["done", "completed"]:
            timer.status = "completed"
            updated_count += 1
            continue

        watchers = await TaskWatcherRepository.list_by_task(db, timer.task.id)
        watcher_ids = {w.user_id for w in watchers}

        recipients = {a.user_id for a in timer.task.assignees if a.user_id is not None}
        recipients.update(watcher_ids)

        if now >= timer.warning_at and not timer.warning_sent and timer.status == "active":
            timer.status = "warning"
            timer.warning_sent = True
            updated_count += 1
            
            for recipient_id in recipients:
                NotificationService.create_notification(
                    org_id=timer.task.org_id,
                    recipient_id=recipient_id,
                    type=NotificationType.SLA_WARNING,
                    actor_id=None,
                    entity_type=NotificationEntityType.TASK,
                    entity_id=timer.task.id,
                    payload={
                        "task_title": timer.task.title,
                        "deadline": timer.deadline.isoformat(),
                        "warning_at": timer.warning_at.isoformat()
                    }
                )

        if now >= timer.deadline:
            timer.status = "breached"
            should_notify = False
            if not timer.breached_sent:
                should_notify = True
            elif timer.last_breached_notification_at is None:
                should_notify = True
            else:
                last_sent = timer.last_breached_notification_at
                if last_sent.tzinfo is None:
                    last_sent = last_sent.replace(timezone.utc)
                if now - last_sent >= timedelta(hours=1):
                    should_notify = True

            if should_notify:
                timer.breached_sent = True
                timer.last_breached_notification_at = now
                updated_count += 1

                for recipient_id in recipients:
                    NotificationService.create_notification(
                        org_id=timer.task.org_id,
                        recipient_id=recipient_id,
                        type=NotificationType.SLA_BREACHED,
                        actor_id=None,
                        entity_type=NotificationEntityType.TASK,
                        entity_id=timer.task.id,
                        payload={
                            "task_title": timer.task.title,
                            "deadline": timer.deadline.isoformat()
                        }
                    )
                    
    if updated_count > 0:
        await db.flush()

    return updated_count
