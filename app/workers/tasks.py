import asyncio
import uuid
import logging
from datetime import date, datetime, time
from sqlalchemy import select
from celery.utils.log import get_task_logger

from app.workers.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.core.redis import redis_client
from app.models.notifications import Notification
from app.models.users import User
from app.models.tasks import Task
from app.models.task_events import TaskEvent
from app.models.automation_rules import AutomationRule
from app.models.org_members import OrgMember

logger = get_task_logger(__name__)


@celery_app.task(name="send_test_notification")
def send_test_notification(message: str) -> str:
    logger.info(f"Received smoke test message: {message}")
    
    # Graceful failure handling test
    if message == "fail":
        raise ValueError("Simulated task failure for verification!")

    with open("celery_smoke_test.log", "a") as f:
        f.write(f"Smoke test message received: {message}\n")

    return f"Processed: {message}"


@celery_app.task(name="send_notification")
def send_notification(
    org_id: str,
    recipient_id: str,
    type: str,
    actor_id: str | None,
    entity_type: str | None,
    entity_id: str | None,
    payload: dict
) -> str:
    logger.info(f"Processing notification type={type} for recipient={recipient_id}")
    
    async def _async_save():
        try:
            o_id = uuid.UUID(org_id)
            r_id = uuid.UUID(recipient_id)
            a_id = uuid.UUID(actor_id) if actor_id else None
            e_id = uuid.UUID(entity_id) if entity_id else None

            async with AsyncSessionLocal() as db:
                notification = Notification(
                    org_id=o_id,
                    recipient_id=r_id,
                    actor_id=a_id,
                    type=type,
                    entity_type=entity_type,
                    entity_id=e_id,
                    payload=payload,
                    is_read=False
                )
                db.add(notification)
                await db.commit()

                receipent = await db.get(User, r_id)
                if receipent and receipent.is_active:
                    redis_key = f"user:{recipient_id}:unread_count"
                    await redis_client.incr(redis_key)
                    logger.info(f"Notification saved to DB and Redis counter incremented for user {recipient_id}")
                else:
                    logger.info(f"Notification saved to DB but Redis count skipped for deactivated/missing user {recipient_id}")
        finally:
            from app.core.database import engine
            await engine.dispose()
            await redis_client.close()
                
    asyncio.run(_async_save())
    return f"Notification {type} sent to {recipient_id}"

@celery_app.task(name="process_automation_events")
def process_automation_events() -> str:

    logger.info("Starting processing of automation events...")
    
    async def _async_process():
        from app.core.enums import NotificationType, NotificationEntityType
        
        try:
            async with AsyncSessionLocal() as db:
                events_result = await db.scalars(
                    select(TaskEvent)
                    .where(TaskEvent.processed == False)
                    .order_by(TaskEvent.created_at.asc())
                )
                events = list(events_result.all())
                
                if not events:
                    logger.info("No unprocessed task events to process.")
                    return
                
                logger.info(f"Found {len(events)} unprocessed events to process.")
                
                for event in events:
                    try:
                        event.processed = True
                        await db.flush()
                        
                        task = await db.get(Task, event.task_id)
                        if not task:
                            logger.warning(f"Task {event.task_id} not found for event {event.id}. Skipping.")
                            await db.commit()
                            continue
                        
                        rules_result = await db.scalars(
                            select(AutomationRule)
                            .where(
                                AutomationRule.org_id == event.org_id,
                                AutomationRule.trigger_event == event.event_type,
                                AutomationRule.is_active == True
                            )
                            .order_by(AutomationRule.created_at.asc())
                        )
                        rules = list(rules_result.all())
                        
                        for rule in rules:
                            if rule.project_id is not None and rule.project_id != task.project_id:
                                continue
                            
                            matched = True
                            conditions = rule.conditions or {}
                            for field, expected_value in conditions.items():
                                val_in_payload = None
                                if event.payload:
                                    if field in event.payload:
                                        val_in_payload = event.payload[field]
                                    elif f"new_{field}" in event.payload:
                                        val_in_payload = event.payload[f"new_{field}"]
                                
                                actual_value = val_in_payload if val_in_payload is not None else getattr(task, field, None)
                                if str(actual_value) != str(expected_value):
                                    matched = False
                                    break
                            
                            if not matched:
                                continue
                            
                            logger.info(f"Rule '{rule.name}' matches event {event.id} on task {task.id}.")
                            
                            action_type = rule.action_type
                            payload = rule.action_payload or {}
                            
                            if action_type == "NOTIFY_USER":
                                recipient_id = payload.get("user_id")
                                message = payload.get("message", f"Automation alert: {rule.name}")
                                if recipient_id:
                                    from app.services.notification_service import NotificationService
                                    NotificationService.create_notification(
                                        org_id=task.org_id,
                                        recipient_id=uuid.UUID(recipient_id),
                                        type=NotificationType.AUTOMATION,
                                        actor_id=None,
                                        entity_type=NotificationEntityType.TASK,
                                        entity_id=task.id,
                                        payload={"message": message, "rule_name": rule.name}
                                    )
                                    
                            elif action_type == "NOTIFY_ROLE":
                                role = payload.get("role")
                                message = payload.get("message", f"Automation alert: {rule.name}")
                                if role:
                                    members_result = await db.scalars(
                                        select(OrgMember.user_id)
                                        .where(
                                            OrgMember.org_id == task.org_id,
                                            OrgMember.role == role
                                        )
                                    )
                                    member_ids = list(members_result.all())
                                    from app.services.notification_service import NotificationService
                                    for mid in member_ids:
                                        NotificationService.create_notification(
                                            org_id=task.org_id,
                                            recipient_id=mid,
                                            type=NotificationType.AUTOMATION,
                                            actor_id=None,
                                            entity_type=NotificationEntityType.TASK,
                                            entity_id=task.id,
                                            payload={"message": message, "rule_name": rule.name}
                                        )
                                        
                            elif action_type == "CHANGE_STATUS":
                                new_status = payload.get("status")
                                if new_status:
                                    task.status = new_status
                                    task.version += 1
                                    await db.flush()
                                    logger.info(f"Rule '{rule.name}' changed task {task.id} status to {new_status}.")
                                    
                            elif action_type == "SEND_EMAIL":
                                email = payload.get("email")
                                subject = payload.get("subject", "Automation Update")
                                body = payload.get("body", "")
                                logger.info(f"Simulating email sent to {email}. Subject: {subject}. Body: {body}")
                        
                        await db.commit()
                    except Exception as e:
                        logger.error(f"Failed to process event {event.id}: {e}")
                        await db.rollback()
                        
        finally:
            from app.core.database import engine
            await engine.dispose()
            await redis_client.close()
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import threading
        t = threading.Thread(target=lambda: asyncio.run(_async_process()))
        t.start()
        t.join()
    else:
        asyncio.run(_async_process())
    return "Event processing complete"

@celery_app.task(name="check_overdue_tasks")
def check_overdue_tasks() -> str:

    logger.info("Scanning for overdue tasks")
    
    async def _async_check():
        
        try:
            async with AsyncSessionLocal() as db:
                today = date.today()
                
                overdue_result = await db.scalars(
                    select(Task)
                    .where(
                        Task.due_date < today,
                        Task.status != "done",
                        Task.deleted_at.is_(None)
                    )
                )
                overdue_tasks = list(overdue_result.all())
                
                logger.info(f"Found {len(overdue_tasks)} potential overdue tasks.")
                
                today_start = datetime.combine(today, time.min)
                event_created = False
                
                for task in overdue_tasks:
                    exists = await db.scalar(
                        select(TaskEvent.id)
                        .where(
                            TaskEvent.task_id == task.id,
                            TaskEvent.event_type == "TASK_OVERDUE",
                            TaskEvent.created_at >= today_start
                        )
                    )
                    
                    if not exists:
                        event = TaskEvent(
                            task_id=task.id,
                            org_id=task.org_id,
                            event_type="TASK_OVERDUE",
                            actor_id=None,
                            payload={
                                "task_title": task.title,
                                "due_date": str(task.due_date)
                            },
                            processed=False
                        )
                        db.add(event)
                        event_created = True
                        logger.info(f"Fired TASK_OVERDUE event for task {task.id}.")
                
                if event_created:
                    await db.commit()
                    process_automation_events.delay()
                    
        finally:
            from app.core.database import engine
            await engine.dispose()
            await redis_client.close()
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import threading
        t = threading.Thread(target=lambda: asyncio.run(_async_check()))
        t.start()
        t.join()
    else:
        asyncio.run(_async_check())
    return "Overdue tasks check complete"