import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.projects import Project
from app.schemas.projects import *
from app.core.database import transaction_scope
from app.repositories.project_repository import ProjectRepository

async def create_project(
        db: AsyncSession,
        org_id: uuid.UUID,
        creator_id: uuid.UUID,
        project_in: ProjectCreate
) -> Project:
    async with transaction_scope(db):
        return await ProjectRepository.create(
            db,
            org_id=org_id,
            name=project_in.name,
            description=project_in.description,
            color=project_in.color,
            created_by=creator_id
        )
    
async def list_projects(
        db: AsyncSession,
        org_id: uuid.UUID,
        status: ProjectStatus | None = None
) -> list[Project]:
    return await ProjectRepository.list_projects(db, org_id, status)

async def get_project(
        db: AsyncSession,
        org_id: uuid.UUID,
        project_id: uuid.UUID
) -> Project:
    project = await ProjectRepository.get_by_id(db, org_id, project_id)
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
        db: AsyncSession,
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

        has_tasks = await ProjectRepository.has_tasks(db, project_id)
        if has_tasks and not cascade:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "CASCADE_REQUIRED",
                    "message": "Project has tasks. Explicit cascade=True is required to delete."
                }
            )
        
        await ProjectRepository.delete(db, project)
