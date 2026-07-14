import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.projects import Project
from app.models.project_statuses import ProjectStatusModel
from app.models.workflow_rules import WorkflowRule
from app.schemas.workflow import ProjectStatusCreate, WorkflowRuleCreate
from app.schemas.projects import *
from app.core.database import transaction_scope
from app.repositories.project_repository import ProjectRepository
from app.repositories.project_status_repository import ProjectStatusRepository
from app.repositories.workflow_rule_repository import WorkflowRuleRepository

async def create_project(
        db: AsyncSession,
        org_id: uuid.UUID,
        creator_id: uuid.UUID,
        project_in: ProjectCreate
) -> Project:
    async with transaction_scope(db):
        project = await ProjectRepository.create(
            db,
            org_id=org_id,
            name=project_in.name,
            description=project_in.description,
            color=project_in.color,
            created_by=creator_id
        )
        
        default_statuses = ["todo", "in_progress", "review", "done"]
        for idx, status_name in enumerate(default_statuses):
            await ProjectStatusRepository.create(
                db=db,
                project_id=project.id,
                org_id=org_id,
                name=status_name,
                position=idx
            )
        return project
    
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

async def create_custom_status(
    db: AsyncSession,
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    payload: ProjectStatusCreate
) -> ProjectStatusModel:
    
    async with transaction_scope(db):
        project = await get_project(db, org_id, project_id)
        
        existing = await ProjectStatusRepository.get_by_project_and_name(db, project_id, payload.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "STATUS_ALREADY_EXISTS",
                    "message": f"A status with name '{payload.name}' already exists in this project."
                }
            )
            
        return await ProjectStatusRepository.create(
            db=db,
            project_id=project_id,
            org_id=org_id,
            name=payload.name,
            color=payload.color,
            position=payload.position
        )
    
async def get_project_statuses(
    db: AsyncSession,
    org_id: uuid.UUID,
    project_id: uuid.UUID
) -> list[ProjectStatusModel]:
    
    await get_project(db, org_id, project_id)
    return await ProjectStatusRepository.list_by_project(db, project_id)

async def create_workflow_rule(
    db: AsyncSession,
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    payload: WorkflowRuleCreate
) -> WorkflowRule:
    
    async with transaction_scope(db):
        await get_project(db, org_id, project_id)
        
        from_status_obj = await ProjectStatusRepository.get_by_project_and_name(db, project_id, payload.from_status)
        to_status_obj = await ProjectStatusRepository.get_by_project_and_name(db, project_id, payload.to_status)
        
        if not from_status_obj or not to_status_obj:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "INVALID_STATUS",
                    "message": "Both source and target statuses must exist in the project."
                }
            )
            
        existing = await WorkflowRuleRepository.get_by_transition(
            db, project_id, payload.from_status, payload.to_status
        )
        if existing:
            return existing
            
        return await WorkflowRuleRepository.create(
            db=db,
            project_id=project_id,
            org_id=org_id,
            from_status=payload.from_status,
            to_status=payload.to_status
        )