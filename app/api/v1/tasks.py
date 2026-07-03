import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_org_member
from app.models.org_members import OrgMember
from app.schemas.tasks import *
from app.services import task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("", response_model=TaskResponse, status_code= status.HTTP_201_CREATED)
async def create_task_route(
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    
    return await task_service.create_task(
        db=db,
        org_id=org_member.org_id,
        creator_id=org_member.user_id,
        task_in=payload
    )

@router.get("",response_model=TaskListResponse)
async def list_tasks_route(

    project_id: uuid.UUID | None = None,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    assigned_to: uuid.UUID | None = None,
    due_date: date | None = None,
    cursor: str | None = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    
    tasks, next_cursor = await task_service.list_tasks(
        db=db,
        org_id=org_member.org_id,
        project_id=project_id,
        status=status,
        priority=priority,
        assigned_to=assigned_to,
        due_date=due_date,
        cursor=cursor,
        limit=limit
    )
    return {"tasks": tasks, "next_cursor": next_cursor}

@router.get("/{id}", response_model=TaskResponse)
async def get_task_route(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    
    return await task_service.get_task(
        db=db,
        org_id= org_member.org_id,
        task_id=id
    )

@router.patch("/{id}", response_model= TaskResponse)
async def update_task_route(
    id: uuid.UUID,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    
    return await task_service.update_task(
        db=db,
        org_id=org_member.org_id,
        task_id=id,
        task_in=payload
    )

@router.patch("/{id}/status", response_model=TaskResponse)
async def update_task_status_route(
    id: uuid.UUID,
    payload: TaskStatusUpdate,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    
    return await task_service.update_task_status(
        db=db,
        org_id=org_member.org_id,
        task_id=id,
        status_in=payload,
        caller_member=org_member
    )

@router.patch("/{id}/assign", response_model= TaskResponse)
async def assign_task_route(
    id: uuid.UUID,
    payload: TaskAssignUpdate,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    return await task_service.assign_task(
        db=db,
        org_id=org_member.org_id,
        task_id=id,
        payload=payload,
        caller_member=org_member
    )

@router.delete("/{id}", status_code= status.HTTP_204_NO_CONTENT)
async def delete_task_route(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    
    await task_service.delete_task(
        db=db,
        org_id=org_member.org_id,
        task_id=id,
        caller_member=org_member
    )

