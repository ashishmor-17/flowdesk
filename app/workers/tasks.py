import asyncio
import uuid
import logging
import threading
from datetime import date, time, timezone, timedelta, datetime
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from celery.utils.log import get_task_logger

from app.workers.celery_app import celery_app
from app.core.database import AsyncSessionLocal, transaction_scope
from app.core.redis import redis_client
from app.models.notifications import Notification
from app.models.users import User
from app.models.tasks import Task
from app.models.task_events import TaskEvent
from app.models.automation_rules import AutomationRule
from app.models.org_members import OrgMember
from app.models.sla_timers import SLATimer
from app.models.task_watchers import TaskWatcher
from app.models.automation_history import AutomationHistory
from app.core.enums import NotificationType, NotificationEntityType
from app.services.notification_service import NotificationService
from app.services.upload_session_service import cleanup_expired_sessions
from app.services.sla_service import scan_and_evaluate_sla_timers

logger = get_task_logger(__name__)

_loop = None
_loop_thread = None
_loop_lock = threading.Lock()


def start_background_loop():
    global _loop, _loop_thread
    with _loop_lock:
        if _loop is None:
            _loop = asyncio.new_event_loop()
            def run_loop(loop):
                asyncio.set_event_loop(loop)
                loop.run_forever()
            _loop_thread = threading.Thread(target=run_loop, args=(_loop,), daemon=True)
            _loop_thread.start()


def run_async_task(coro_func):

    start_background_loop()
    coro = coro_func()
    future = asyncio.run_coroutine_threadsafe(coro, _loop)
    return future.result()


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
                try:
                    await redis_client.incr(redis_key)
                    logger.info(f"Notification saved to DB and Redis counter incremented for user {recipient_id}")
                except Exception as e:
                    logger.warning(f"Notification saved to DB, but failed to increment Redis count: {e}")
            else:
                logger.info(f"Notification saved to DB but Redis count skipped for deactivated/missing user {recipient_id}")
                
    run_async_task(_async_save)
    return f"Notification {type} sent to {recipient_id}"


@celery_app.task(name="process_automation_events")
def process_automation_events() -> str:
    logger.info("Starting processing of automation events")
    
    async def _async_process():
        try:
            async with AsyncSessionLocal() as db:
                events_result = await db.scalars(
                    select(TaskEvent)
                    .where(TaskEvent.processed == False)
                    .order_by(TaskEvent.created_at.asc())
                )
                events = list(events_result.all())
                
                logger.info(f"Found {len(events)} unprocessed events.")
                
                if not events:
                    return
                
                for event in events:
                    try:
                        logger.info(f"Processing event {event.id} for task {event.task_id}...")
                        event.processed = True
                        await db.commit()
                        logger.info(f"Marked event {event.id} as processed and committed.")
                        
                        task = await db.get(Task, event.task_id)
                        if not task:
                            logger.error(f"Task {event.task_id} not found.")
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
                        logger.info(f"Found {len(rules)} rules for event {event.id}.")
                        
                        for rule in rules:
                            if rule.project_id is not None and rule.project_id != task.project_id:
                                logger.info(f"Rule {rule.name} project mismatch.")
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
                                logger.info(f"Rule {rule.name} conditions not matched.")
                                continue
                            
                            logger.info(f"Rule '{rule.name}' matched.")
                            
                            rule_id = rule.id
                            event_id = event.id
                            task_id = task.id
                            action_type = rule.action_type
                            payload = rule.action_payload or {}
                            
                            success = True
                            error_message = None
                            
                            try:
                                logger.info(f"Executing action {action_type}...")
                                if action_type == "NOTIFY_USER":
                                    recipient_id = payload.get("user_id")
                                    message = payload.get("message", f"Automation alert: {rule.name}")
                                    if recipient_id:
                                        NotificationService.create_notification(
                                            org_id=task.org_id,
                                            recipient_id=uuid.UUID(recipient_id),
                                            type=NotificationType.AUTOMATION,
                                            actor_id=None,
                                            entity_type=NotificationEntityType.TASK,
                                            entity_id=task_id,
                                            payload={"message": message, "rule_name": rule.name}
                                        )
                                    else:
                                        raise ValueError("Recipient user_id is missing in action payload.")
                                        
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
                                        for mid in member_ids:
                                            NotificationService.create_notification(
                                                org_id=task.org_id,
                                                recipient_id=mid,
                                                type=NotificationType.AUTOMATION,
                                                actor_id=None,
                                                entity_type=NotificationEntityType.TASK,
                                                entity_id=task_id,
                                                payload={"message": message, "rule_name": rule.name}
                                            )
                                    else:
                                        raise ValueError("Recipient role is missing in action payload.")
                                            
                                elif action_type == "CHANGE_STATUS":
                                    new_status = payload.get("status")
                                    if new_status:
                                        task.status = new_status
                                        task.version += 1
                                        await db.flush()
                                        logger.info(f"Changed status of task {task_id} to {new_status}.")
                                    else:
                                        raise ValueError("Status is missing in action payload.")
                                        
                                elif action_type == "SEND_EMAIL":
                                    email = payload.get("email")
                                    subject = payload.get("subject", "Automation Update")
                                    body = payload.get("body", "")
                                    if not email:
                                        raise ValueError("Recipient email is missing in action payload.")
                                    logger.info(f"Simulating email sent to {email}.")
                                else:
                                    raise ValueError(f"Unknown action type: {action_type}")
                                
                                await db.commit()
                                logger.info("Action completed and transaction committed.")
                            except Exception as e:
                                await db.rollback()
                                success = False
                                error_message = str(e)
                                logger.error(f"Action failed with error: {e}", exc_info=True)
                            
                            try:
                                logger.info("Writing history record...")
                                history = AutomationHistory(
                                    rule_id=rule_id,
                                    event_id=event_id,
                                    task_id=task_id,
                                    success=success,
                                    error_message=error_message,
                                    action_type=action_type
                                )
                                db.add(history)
                                await db.commit()
                                logger.info("History record committed successfully.")
                            except Exception as e:
                                logger.error(f"Failed to commit history: {e}", exc_info=True)
                                await db.rollback()
                    except Exception as e:
                        logger.error(f"Failed to process event {event.id}: {e}", exc_info=True)
                        await db.rollback()
        except Exception as e:
            logger.error(f"Top level error in automation worker: {e}", exc_info=True)

    run_async_task(_async_process)
    return "Event processing complete"


@celery_app.task(name="check_overdue_tasks")
def check_overdue_tasks() -> str:
    logger.info("Scanning for overdue tasks")
    
    async def _async_check():
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
                
    run_async_task(_async_check)
    return "Overdue tasks check complete"


@celery_app.task(name="cleanup_expired_upload_sessions")
def cleanup_expired_upload_sessions() -> str:
    logger.info("Scanning for expired upload sessions to clean up")
    
    async def _async_cleanup():
        async with AsyncSessionLocal() as db:
            count = await cleanup_expired_sessions(db)
            logger.info(f"Cleaned up {count} expired upload sessions.")

    run_async_task(_async_cleanup)
    return "Cleanup of expired upload sessions complete"


@celery_app.task(name="check_sla_timers")
def check_sla_timers() -> str:
    logger.info("Scanning active SLA timers for warning/breach escalation")

    async def _async_check():
        async with AsyncSessionLocal() as db:
            count = await scan_and_evaluate_sla_timers(db)
            if count > 0:
                await db.commit()
            logger.info(f"SLA timers check processed and committed {count} changes.")

    run_async_task(_async_check)
    return "SLA timers check complete"