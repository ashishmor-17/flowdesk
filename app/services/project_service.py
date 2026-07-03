import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.projects import Project
from app.models.tasks import Task
from app.schemas.projects import *
from app.core.database import transaction_scope
from app.core.errors import ErrorCode

async def create_project(
        db: AsyncSession,
        org_id: uuid.UUID,
        creator_id: uuid.UUID,
        project_in: ProjectCreate
) -> Project:
    
    async with transaction_scope(db):
        project = Project(
            org_id= org_id,
            name= project_in.name,
            description= project_in.description,
            color= project_in.color,
            created_by= creator_id
        )

        db.add(project)
        await db.flush()

        return project
    
async def list_projects(
        db: AsyncSession,
        org_id: uuid.UUID,
        status: ProjectStatus | None = None
) -> list[Project]:
    
    query = select(Project).where(Project.org_id == org_id)
    if status is not None:
        query = query.where(Project.status == status)

    result = await db.scalars(query)
    return list(result.all())

async def get_project(
        db: AsyncSession,
        org_id: uuid.UUID,
        project_id: uuid.UUID
) -> Project:
    
    project = await db.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.org_id == org_id
        )
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PROJECT_NOT_FOUND",
                "message": "Project not found or you do not have access."
            }
        )
    return project

async def update_project(
        db: AsyncSession,
        org_id: uuid.UUID,
        project_id: uuid.UUID,
        project_in: ProjectCreate
) -> Project:
    
    async with transaction_scope(db):
        project = await get_project(db, org_id, project_id)

        update_data = project_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)

        await db.flush()
        await db.refresh(project)

        return project
    
async def archive_project(
        db:AsyncSession,
        org_id: uuid.UUID,
        project_id: uuid.UUID
) -> Project:
    
    async with transaction_scope(db):
        project = await get_project(db, org_id, project_id)
        project.status = ProjectStatus.ARCHIVED
        return project
    
async def delete_project(
        db: AsyncSession,
        org_id: uuid.UUID,
        project_id: uuid.UUID,
        cascade: bool = False
) -> None:
    
    async with transaction_scope(db):
        project = await get_project(db, org_id, project_id)

        has_tasks = await db.scalar(
            select(Task)
            .where(Task.project_id == project_id).limit(1)
        ) is not None

        if has_tasks and not cascade:
            raise HTTPException(
                status_code= status.HTTP_400_BAD_REQUEST,
                detail= {
                    "code": "CASCADE_REQUIRED",
                    "message": "Project has tasks. Explicit cascade=True is required to delete."
                }
            )
        
        await db.delete(project)

