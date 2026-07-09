import uuid
import base64
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.models.tasks import Task
from app.models.task_assignees import TaskAssignee
from app.models.org_members import OrgMember
from app.models.users import User
from app.schemas.tasks import *
from app.services import project_service
from app.core.database import transaction_scope
from app.services.notification_service import NotificationService
from app.core.enums import ProjectStatus, TASK_STATE_TRANSITIONS, UserRole, NotificationEntityType, NotificationType

async def create_task(
        db: AsyncSession,
        org_id: uuid.UUID,
        creator_id: uuid.UUID,
        task_in: TaskCreate
) -> Task:
    
    async with transaction_scope(db):
        project = await project_service.get_project(db, org_id, task_in.project_id)

        if project.status == ProjectStatus.ARCHIVED:
            raise HTTPException(
                status_code= status.HTTP_403_FORBIDDEN,
                detail= {
                    "code": "PROJECT_ARCHIVED",
                    "message": "Can not create tasks in an archived projects."
                }
            )

        task = Task(
            project_id=task_in.project_id,
            org_id=org_id,
            title=task_in.title,
            description=task_in.description,
            priority=task_in.priority,
            due_date=task_in.due_date,
            created_by=creator_id
        )

        db.add(task)
        await db.flush()

        from app.services.event_service import fire_task_event
        await fire_task_event(
            db=db,
            task_id=task.id,
            org_id=org_id,
            event_type="TASK_CREATED",
            actor_id=creator_id,
            payload={
                "task_title": task.title,
                "project_id": str(task.project_id),
                "priority": str(task.priority),
                "status": str(task.status)
            }
        )

        return await get_task(db, org_id, task.id)
    
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
    
    # Base query with eager loading for assignees (avoids N+1 query problem)
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
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_CURSOR",
                    "message": "Invalid pagination cursor"
                }
            )
        
    result = await db.execute(query.limit(limit + 1))
    tasks = list(result.scalars().all())  # Note the parenthesis here!

    next_cursor = None

    if len(tasks) > limit:
        tasks = tasks[:limit]
        last_task = tasks[-1]

        cursor_str = f"{last_task.created_at.isoformat()}_{last_task.id}"
        next_cursor = base64.b64encode(cursor_str.encode()).decode()

    return tasks, next_cursor

async def get_task(
        db: AsyncSession,
        org_id: uuid.UUID,
        task_id: uuid.UUID
) -> Task:
    
    query = (
        select(Task)
        .where(
            Task.id == task_id,
            Task.org_id == org_id,
            Task.deleted_at.is_(None)
        )
        .options(
            selectinload(Task.assignees),
            selectinload(Task.labels)
        )
    )

    result = await db.execute(query)
    task = result.scalars().first()

    if not task:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail= {
                "code": "TASK_NOT_FOUND",
                "message": "Task not found."
            }
        )
    
    return task

async def update_task(
        db: AsyncSession,
        org_id: uuid.UUID,
        task_id: uuid.UUID,
        task_in: TaskUpdate
) -> Task:
    
    async with transaction_scope(db):
        task = await get_task(db, org_id, task_id)

        if task.version != task_in.version:
            raise HTTPException(
                status_code= status.HTTP_409_CONFLICT,
                detail= {
                    "code": "VERSION_MISMATCH",
                    "message": "Task has been updated by another user. Please refresh and try again."
                }
            )
        
        update_data = task_in.model_dump(exclude_unset=True, exclude={"version"})
        for field, value in update_data.items():
            setattr(task, field, value)

        task.version +=1

        await db.flush()

        return await get_task(db, org_id, task.id)
    
async def update_task_status(
        db: AsyncSession,
        org_id: uuid.UUID,
        task_id: uuid.UUID,
        status_in: TaskStatusUpdate,
        caller_member: OrgMember
) -> Task:
    
    async with transaction_scope(db):
        task = await get_task(db, org_id, task_id)

        if task.version != status_in.version:
            raise HTTPException(
                status_code= status.HTTP_409_CONFLICT,
                detail= {
                    "code": "VERSION_MISMATCH",
                    "message": "Task has been updated by another user. Please refresh and try again."
                }
            )
        
        allowed_next_states = TASK_STATE_TRANSITIONS.get(task.status, set())

        if status_in.status not in allowed_next_states:
            raise HTTPException(
                status_code= status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail= {
                    "code": "INVALID_STATUS_TRANSITION",
                    "message": f"Can not transition task from {task.status.upper()} to {status_in.status.upper()}."
                }
            )
        
        old_status = task.status
        new_status = status_in.status
        task.status = new_status
        task.version += 1
        await db.flush()

        if old_status != new_status:
            from app.services.event_service import fire_task_event
            await fire_task_event(
                db=db,
                task_id=task.id,
                org_id=org_id,
                event_type="STATUS_CHANGED",
                actor_id=caller_member.user_id,
                payload={
                    "old_status": str(old_status),
                    "new_status": str(new_status),
                    "task_title": task.title
                }
            )

            caller_user = await db.get(User, caller_member.user_id)
            caller_name = f"{caller_user.first_name} {caller_user.last_name}" if caller_user.last_name else caller_user.first_name

            for assignee in task.assignees:
                if assignee.user_id != caller_member.user_id:
                    NotificationService.create_notification(
                        org_id=org_id,
                        recipient_id=assignee.user_id,
                        type=NotificationType.TASK_STATUS_CHANGE,
                        actor_id=caller_member.user_id,
                        entity_type=NotificationEntityType.TASK,
                        entity_id=task.id,
                        payload={
                            "task_id": str(task.id),
                            "task_title": task.title,
                            "old_status": old_status,
                            "new_status": new_status,
                            "changed_by_name": caller_name
                        }
                    )

        return await get_task(db, org_id, task.id)
    
async def assign_task(
        db: AsyncSession,
        org_id: uuid.UUID,
        task_id: uuid.UUID,
        payload: TaskAssignUpdate,
        caller_member: OrgMember
) -> Task:
    
    async with transaction_scope(db):
        task = await get_task(db, org_id, task_id)
        user_ids = payload.user_ids

        other_ids = [uid for uid in user_ids if uid != caller_member.user_id]
        if other_ids and caller_member.role not in [UserRole.ADMIN, UserRole.OWNER]:
            raise HTTPException(
                status_code= status.HTTP_403_FORBIDDEN,
                detail= {
                    "code": "FORBIDDEN",
                    "message": "Only Admin or Owner can assign tasks to other users."
                }
            )
        
        if user_ids:
            query = select(OrgMember.user_id).where(
                OrgMember.org_id == org_id,
                OrgMember.user_id.in_(user_ids)
            )
            result = await db.execute(query)
            existing_member_ids = set(result.scalars().all())

            if (len(existing_member_ids) != len(set(user_ids))):
                raise HTTPException(
                    status_code= status.HTTP_400_BAD_REQUEST,
                    detail= {
                        "code": "INVALID_ASSIGNEE",
                        "message": "One or more assigned users are not members of this organization."
                    }
                )
            
        current_assignee_ids = {a.user_id for a in task.assignees}
        newly_assigned_ids = [uid for uid in user_ids if uid not in current_assignee_ids]
        unassigned_ids = [uid for uid in current_assignee_ids if uid not in user_ids]

        task.assignees = [a for a in task.assignees if a.user_id in user_ids]

        for uid in user_ids:
            if uid not in current_assignee_ids:
                new_assignee = TaskAssignee(
                    task_id= task_id,
                    user_id= uid,
                    assigned_by= caller_member.user_id
                )
                task.assignees.append(new_assignee)

        await db.flush()

        if newly_assigned_ids:
            from app.services.event_service import fire_task_event
            await fire_task_event(
                db=db,
                task_id=task.id,
                org_id=org_id,
                event_type="TASK_ASSIGNED",
                actor_id=caller_member.user_id,
                payload={
                    "newly_assigned_ids": [str(uid) for uid in newly_assigned_ids],
                    "task_title": task.title
                }
            )

        caller_user = await db.get(User, caller_member.user_id)
        caller_name = f"{caller_user.first_name} {caller_user.last_name}" if caller_user.last_name else caller_user.first_name

        for uid in newly_assigned_ids:
            if uid != caller_member.user_id:
                NotificationService.create_notification(
                    org_id=org_id,
                    recipient_id=uid,
                    type=NotificationType.TASK_ASSIGNED,
                    actor_id=caller_member.user_id,
                    entity_type=NotificationEntityType.TASK,
                    entity_id=task.id,
                    payload={
                        "task_id": str(task.id),
                        "task_title": task.title,
                        "assigned_by_name": caller_name
                    }
                )

        for uid in unassigned_ids:
            if uid != caller_member.user_id:
                NotificationService.create_notification(
                    org_id=org_id,
                    recipient_id=uid,
                    type=NotificationType.TASK_UNASSIGNED,
                    actor_id=caller_member.user_id,
                    entity_type=NotificationEntityType.TASK,
                    entity_id=task.id,
                    payload={
                        "task_id": str(task.id),
                        "task_title": task.title,
                        "unassigned_by_name": caller_name
                    }
                )
        
        return await get_task(db, org_id, task.id)
    
async def delete_task(
        db: AsyncSession,
        org_id: uuid.UUID,
        task_id: uuid.UUID,
        caller_member: OrgMember
) -> None:
    
    async with transaction_scope(db):
        if caller_member.role not in [UserRole.ADMIN, UserRole.OWNER]:
            raise HTTPException(
                status_code= status.HTTP_403_FORBIDDEN,
                detail= {
                    "code": "FORBIDDEN",
                    "message": "Only Admin or Owner can delete tasks."
                }
            )
        
        task = await get_task(db, org_id, task_id)

        task.soft_delete()
        await db.flush()

