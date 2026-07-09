import uuid
import base64
from datetime import date, datetime
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.models.tasks import Task
from app.models.task_assignees import TaskAssignee
from app.models.org_members import OrgMember
from app.core.enums import TaskStatus, TaskPriority

class TaskRepository:
    @staticmethod
    async def get_by_id(db: AsyncSession, org_id: uuid.UUID, task_id: uuid.UUID) -> Task | None:
        
        query = (
            select(Task)
            .where(Task.org_id == org_id, Task.id == task_id, Task.deleted_at.is_(None))
            .options(
                selectinload(Task.assignees),
                selectinload(Task.labels)
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_tasks(
        db: AsyncSession,
        org_id: uuid.UUID,
        project_id: uuid.UUID | None = None,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        assigned_to: uuid.UUID | None = None,
        due_date: date | None = None,
        cursor: str | None = None,
        limit: int = 20
    ) -> tuple[list[Task], str | None]:
        
        query = (
            select(Task)
            .where(Task.org_id == org_id, Task.deleted_at.is_(None))
            .options(
                selectinload(Task.assignees),
                selectinload(Task.labels)
            )
            .order_by(Task.created_at.desc(), Task.id.desc())
        )

        if project_id:
            query = query.where(Task.project_id == project_id)

        if status:
            query = query.where(Task.status == status)

        if priority:
            query = query.where(Task.priority == priority)

        if due_date:
            query = query.where(Task.due_date == due_date)

        if assigned_to:
            query = query.join(Task.assignees).where(TaskAssignee.user_id == assigned_to)

        if cursor:
            try:
                decoded = base64.b64decode(cursor.encode()).decode()
                cursor_time_str, cursor_id_str = decoded.split("_")
                cursor_time = datetime.fromisoformat(cursor_time_str)
                cursor_id = uuid.UUID(cursor_id_str)

                query = query.where(
                    or_(
                        Task.created_at < cursor_time,
                        and_(
                            Task.created_at == cursor_time,
                            Task.id < cursor_id
                        )
                    )
                )
            except Exception:
                raise ValueError("Invalid pagination cursor")

        result = await db.execute(query.limit(limit + 1))
        tasks = list(result.scalars().all())

        next_cursor = None
        if len(tasks) > limit:
            tasks = tasks[:limit]
            last_task = tasks[-1]
            cursor_str = f"{last_task.created_at.isoformat()}_{last_task.id}"
            next_cursor = base64.b64encode(cursor_str.encode()).decode()

        return tasks, next_cursor

    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        project_id: uuid.UUID,
        org_id: uuid.UUID,
        title: str,
        description: str | None = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        due_date: date | None = None,
        created_by: uuid.UUID
    ) -> Task:
        
        task = Task(
            project_id=project_id,
            org_id=org_id,
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            created_by=created_by
        )
        db.add(task)
        await db.flush()
        return task

    @staticmethod
    async def check_members_exist(db: AsyncSession, org_id: uuid.UUID, user_ids: Sequence[uuid.UUID]) -> set[uuid.UUID]:
        
        query = select(OrgMember.user_id).where(
            OrgMember.org_id == org_id,
            OrgMember.user_id.in_(user_ids)
        )
        result = await db.execute(query)
        return set(result.scalars().all())
