import uuid
import base64
from datetime import date
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.tasks import Task
from app.models.task_assignees import TaskAssignee
from app.models.org_members import OrgMember
from app.models.users import User
from app.models.task_watchers import TaskWatcher
from app.schemas.tasks import *
from app.services import project_service
from app.core.database import transaction_scope
from app.services.notification_service import NotificationService
from app.core.enums import ProjectStatus, TASK_STATE_TRANSITIONS, UserRole, NotificationEntityType, NotificationType
from app.repositories.task_repository import TaskRepository
from app.repositories.project_status_repository import ProjectStatusRepository
from app.repositories.workflow_rule_repository import WorkflowRuleRepository
from app.repositories.task_watcher_repository import TaskWatcherRepository
from app.repositories.team_repository import TeamRepository

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

        task = await TaskRepository.create(
            db,
            project_id=task_in.project_id,
            org_id=org_id,
            title=task_in.title,
            description=task_in.description,
            priority=task_in.priority,
            due_date=task_in.due_date,
            created_by=creator_id
        )

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
    try:
        return await TaskRepository.list_tasks(
            db=db,
            org_id=org_id,
            project_id=project_id,
            status=status,
            priority=priority,
            assigned_to=assigned_to,
            due_date=due_date,
            cursor=cursor,
            limit=limit
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_CURSOR",
                "message": str(e)
            }
        )

async def get_task(
        db: AsyncSession,
        org_id: uuid.UUID,
        task_id: uuid.UUID
) -> Task:
    task = await TaskRepository.get_by_id(db, org_id, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "TASK_NOT_FOUND",
                "message": "Task not found or you do not have access."
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
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "VERSION_MISMATCH",
                    "message": "Task has been updated by another user."
                }
            )

        update_data = task_in.model_dump(exclude_unset=True)
        update_data.pop("version", None)
        for field, value in update_data.items():
            setattr(task, field, value)

        task.version += 1
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

        new_status = status_in.status
        old_status = task.status

        if task.version != status_in.version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "VERSION_MISMATCH",
                    "message": "Task has been updated by another user."
                }
            )

        statuses = await ProjectStatusRepository.list_by_project(db, task.project_id)
        
        valid_status_names = [s.name for s in statuses]
        if not valid_status_names:
            valid_status_names = [TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.REVIEW, TaskStatus.DONE]
            
        if new_status not in valid_status_names:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "INVALID_STATUS",
                    "message": f"Status '{new_status}' does not exist in this project."
                }
            )

        rules = await WorkflowRuleRepository.list_by_project(db, task.project_id)
        
        if not rules:
            try:
                old_status_enum = TaskStatus(old_status)
                new_status_enum = TaskStatus(new_status)
                if new_status_enum not in TASK_STATE_TRANSITIONS[old_status_enum]:
                    raise ValueError()
            except (ValueError, KeyError):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "code": "INVALID_STATUS_TRANSITION",
                        "message": f"Cannot transition task from {old_status} to {new_status}."
                    }
                )
        else:
            allowed = any(r.from_status == old_status and r.to_status == new_status for r in rules)
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "code": "INVALID_STATUS_TRANSITION",
                        "message": f"Transition from '{old_status}' to '{new_status}' is blocked by workflow rules."
                    }
                )


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
            caller_name = caller_user.full_name or caller_user.email

            recipients = {a.user_id for a in task.assignees if a.user_id is not None}
            
            watchers = await TaskWatcherRepository.list_by_task(db, task.id)
            recipients.update(w.user_id for w in watchers)

            for recipient_id in recipients:
                if recipient_id != caller_member.user_id:
                    NotificationService.create_notification(
                        org_id=org_id,
                        recipient_id=recipient_id,
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
        
        user_ids = payload.user_ids or []
        team_ids = payload.team_ids or []

        is_admin_or_owner = caller_member.role.lower() in ["owner", "admin"]
        
        other_ids = [uid for uid in user_ids if uid != caller_member.user_id]
        if (other_ids or team_ids) and not is_admin_or_owner:
            raise HTTPException(
                status_code= status.HTTP_403_FORBIDDEN,
                detail= {
                    "code": "FORBIDDEN",
                    "message": "Only Admin or Owner can assign tasks to other users/teams."
                }
            )
        
        if user_ids:
            existing_member_ids = await TaskRepository.check_members_exist(db, org_id, user_ids)
            if len(existing_member_ids) != len(set(user_ids)):
                raise HTTPException(
                    status_code= status.HTTP_400_BAD_REQUEST,
                    detail= {
                        "code": "INVALID_ASSIGNEE",
                        "message": "One or more assigned users are not members of this organization."
                    }
                )

        if team_ids:
            existing_team_ids = await TaskRepository.check_teams_exist(db, org_id, team_ids)
            if len(existing_team_ids) != len(set(team_ids)):
                raise HTTPException(
                    status_code= status.HTTP_400_BAD_REQUEST,
                    detail= {
                        "code": "INVALID_ASSIGNEE",
                        "message": "One or more assigned teams do not exist in this organization."
                    }
                )

        # Update relationships
        task.assignees = [
            a for a in task.assignees 
            if (a.assignee_type == "USER" and a.user_id in user_ids) or
               (a.assignee_type == "TEAM" and a.team_id in team_ids)
        ]

        current_user_ids = {a.user_id for a in task.assignees if a.assignee_type == "USER"}
        current_team_ids = {a.team_id for a in task.assignees if a.assignee_type == "TEAM"}

        caller_user = await db.get(User, caller_member.user_id)
        caller_name = caller_user.full_name or caller_user.email

        for uid in user_ids:
            if uid not in current_user_ids:
                new_assignee = TaskAssignee(
                    task_id=task_id,
                    user_id=uid,
                    assignee_type="USER",
                    assigned_by=caller_member.user_id
                )
                task.assignees.append(new_assignee)
                if uid != caller_member.user_id:
                    NotificationService.create_notification(
                        org_id=org_id,
                        recipient_id=uid,
                        type=NotificationType.TASK_ASSIGNED,
                        actor_id=caller_member.user_id,
                        entity_type=NotificationEntityType.TASK,
                        entity_id=task_id,
                        payload={
                            "task_id": str(task_id),
                            "task_title": task.title,
                            "assigned_by_name": caller_name
                        }
                    )

        for tid in team_ids:
            if tid not in current_team_ids:
                new_assignee = TaskAssignee(
                    task_id=task_id,
                    team_id=tid,
                    assignee_type="TEAM",
                    assigned_by=caller_member.user_id
                )
                task.assignees.append(new_assignee)
                team_member_ids = await TeamRepository.list_member_ids(db, tid)
                for member_uid in team_member_ids:
                    if member_uid != caller_member.user_id:
                        NotificationService.create_notification(
                            org_id=org_id,
                            recipient_id=member_uid,
                            type=NotificationType.TASK_ASSIGNED,
                            actor_id=caller_member.user_id,
                            entity_type=NotificationEntityType.TASK,
                            entity_id=task_id,
                            payload={
                                "task_id": str(task_id),
                                "task_title": task.title,
                                "assigned_by_name": caller_name,
                                "team_id": str(tid)
                            }
                        )

        await db.flush()

        from app.services.event_service import fire_task_event
        await fire_task_event(
            db=db,
            task_id=task.id,
            org_id=org_id,
            event_type="TASK_ASSIGNED",
            actor_id=caller_member.user_id,
            payload={
                "task_title": task.title,
                "assigned_users": [str(uid) for uid in user_ids],
                "assigned_teams": [str(tid) for tid in team_ids]
            }
        )

        return await get_task(db, org_id, task_id)    
    
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

async def add_task_assignee(
    db: AsyncSession,
    org_id: uuid.UUID,
    task_id: uuid.UUID,
    payload: TaskAssigneeCreate,
    caller_member: OrgMember
) -> Task:
    
    async with transaction_scope(db):
        task = await get_task(db, org_id, task_id)
        is_admin_or_owner = caller_member.role.lower() in ["owner", "admin"]
        
        if payload.assignee_type.upper() == "USER":
            user_id = payload.assignee_id
            if user_id != caller_member.user_id and not is_admin_or_owner:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only Admin or Owner can assign tasks to other users."
                )
            member_exists = await TaskRepository.check_members_exist(db, org_id, [user_id])
            if not member_exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is not a member of this organization."
                )
            
            already_assigned = any(a.user_id == user_id for a in task.assignees)
            if not already_assigned:
                new_assignee = TaskAssignee(
                    task_id=task_id,
                    user_id=user_id,
                    assignee_type="USER",
                    assigned_by=caller_member.user_id
                )
                task.assignees.append(new_assignee)
                if user_id != caller_member.user_id:
                    caller_user = await db.get(User, caller_member.user_id)
                    caller_name = caller_user.full_name or caller_user.email
                    NotificationService.create_notification(
                        org_id=org_id,
                        recipient_id=user_id,
                        type=NotificationType.TASK_ASSIGNED,
                        actor_id=caller_member.user_id,
                        entity_type=NotificationEntityType.TASK,
                        entity_id=task_id,
                        payload={
                            "task_id": str(task_id),
                            "task_title": task.title,
                            "assigned_by_name": caller_name
                        }
                    )
                
        elif payload.assignee_type.upper() == "TEAM":
            team_id = payload.assignee_id
            if not is_admin_or_owner:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only Admin or Owner can assign teams to tasks."
                )
            
            teams_exist = await TaskRepository.check_teams_exist(db, org_id, [team_id])
            if not teams_exist:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Team not found in this organization."
                )
                
            already_assigned = any(a.team_id == team_id for a in task.assignees)
            if not already_assigned:
                new_assignee = TaskAssignee(
                    task_id=task_id,
                    team_id=team_id,
                    assignee_type="TEAM",
                    assigned_by=caller_member.user_id
                )
                task.assignees.append(new_assignee)
                team_member_ids = await TeamRepository.list_member_ids(db, team_id)
                caller_user = await db.get(User, caller_member.user_id)
                caller_name = caller_user.full_name or caller_user.email
                for member_uid in team_member_ids:
                    if member_uid != caller_member.user_id:
                        NotificationService.create_notification(
                            org_id=org_id,
                            recipient_id=member_uid,
                            type=NotificationType.TASK_ASSIGNED,
                            actor_id=caller_member.user_id,
                            entity_type=NotificationEntityType.TASK,
                            entity_id=task_id,
                            payload={
                                "task_id": str(task_id),
                                "task_title": task.title,
                                "assigned_by_name": caller_name,
                                "team_id": str(team_id)
                            }
                        )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid assignee type."
            )
            
        await db.flush()

        from app.services.event_service import fire_task_event
        await fire_task_event(
            db=db,
            task_id=task.id,
            org_id=org_id,
            event_type="TASK_ASSIGNED",
            actor_id=caller_member.user_id,
            payload={
                "task_title": task.title,
                "assigned_assignee_id": str(payload.assignee_id),
                "assigned_assignee_type": payload.assignee_type
            }
        )

        return await get_task(db, org_id, task.id)

async def add_task_watcher(
    db: AsyncSession,
    org_id: uuid.UUID,
    task_id: uuid.UUID,
    user_id: uuid.UUID
) -> None:
    
    async with transaction_scope(db):
        task = await get_task(db, org_id, task_id)
        
        existing = await TaskWatcherRepository.get(db, task_id, user_id)
        if existing:
            return
            
        await TaskWatcherRepository.create(db, task_id=task_id, user_id=user_id, org_id=org_id)

async def remove_task_watcher(
    db: AsyncSession,
    org_id: uuid.UUID,
    task_id: uuid.UUID,
    user_id: uuid.UUID,
    caller_member: OrgMember
) -> None:
    
    async with transaction_scope(db):
        await get_task(db, org_id, task_id)
        
        if caller_member.user_id != user_id and caller_member.role not in [UserRole.ADMIN, UserRole.OWNER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "message": "Only the user themselves or organization administrators can remove watchers."
                }
            )
            
        watcher = await TaskWatcherRepository.get(db, task_id, user_id)
        if watcher:
            await TaskWatcherRepository.delete(db, watcher)