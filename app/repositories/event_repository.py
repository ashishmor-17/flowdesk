import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task_events import TaskEvent

class EventRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        task_id: uuid.UUID,
        org_id: uuid.UUID,
        event_type: str,
        actor_id: uuid.UUID | None = None,
        payload: dict | None = None,
        processed: bool = False
    ) -> TaskEvent:
        
        event = TaskEvent(
            task_id=task_id,
            org_id=org_id,
            event_type=event_type,
            actor_id=actor_id,
            payload=payload,
            processed=processed
        )
        db.add(event)
        await db.flush()
        return event
