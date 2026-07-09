import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task_events import TaskEvent
from app.repositories.event_repository import EventRepository

async def fire_task_event(
    db: AsyncSession,
    task_id: uuid.UUID,
    org_id: uuid.UUID,
    event_type: str,
    actor_id: uuid.UUID | None = None,
    payload: dict | None = None
) -> TaskEvent:
    event = await EventRepository.create(
        db,
        task_id=task_id,
        org_id=org_id,
        event_type=event_type,
        actor_id=actor_id,
        payload=payload,
        processed=False
    )
    
    from app.workers.tasks import process_automation_events
    process_automation_events.apply_async(countdown=1)
    
    return event
