import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task_events import TaskEvent

async def fire_task_event(
    db: AsyncSession,
    task_id: uuid.UUID,
    org_id: uuid.UUID,
    event_type: str,
    actor_id: uuid.UUID | None = None,
    payload: dict | None = None
) -> TaskEvent:

    event = TaskEvent(
        task_id=task_id,
        org_id=org_id,
        event_type=event_type,
        actor_id=actor_id,
        payload=payload,
        processed=False
    )
    db.add(event)
    await db.flush()
    
    # using 1-second countdown to ensure the current database transaction
    # has fully committed before the worker tries to query the event.
    from app.workers.tasks import process_automation_events
    process_automation_events.apply_async(countdown=1)
    
    return event
