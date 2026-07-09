import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.projects import Project
from app.models.tasks import Task
from app.core.enums import ProjectStatus

class ProjectRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        org_id: uuid.UUID,
        name: str,
        description: str | None = None,
        color: str | None = None,
        created_by: uuid.UUID
    ) -> Project:
        
        project = Project(
            org_id=org_id,
            name=name,
            description=description,
            color=color,
            created_by=created_by
        )
        db.add(project)
        await db.flush()
        return project

    @staticmethod
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

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        org_id: uuid.UUID,
        project_id: uuid.UUID
    ) -> Project | None:
       
        return await db.scalar(
            select(Project).where(
                Project.id == project_id,
                Project.org_id == org_id
            )
        )

    @staticmethod
    async def has_tasks(db: AsyncSession, project_id: uuid.UUID) -> bool:
        
        task = await db.scalar(
            select(Task).where(Task.project_id == project_id).limit(1)
        )
        return task is not None

    @staticmethod
    async def delete(db: AsyncSession, project: Project) -> None:
        
        await db.delete(project)
