import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.project_statuses import ProjectStatusModel

class ProjectStatusRepository:
    @staticmethod
    async def list_by_project(db: AsyncSession, project_id: uuid.UUID) -> list[ProjectStatusModel]:
        result = await db.scalars(
            select(ProjectStatusModel)
            .where(ProjectStatusModel.project_id == project_id)
            .order_by(ProjectStatusModel.position.asc(), ProjectStatusModel.name.asc())
        )
        return list(result.all())

    @staticmethod
    async def get_by_project_and_name(db: AsyncSession, project_id: uuid.UUID, name: str) -> ProjectStatusModel | None:
        return await db.scalar(
            select(ProjectStatusModel).where(
                ProjectStatusModel.project_id == project_id,
                ProjectStatusModel.name == name
            )
        )

    @staticmethod
    async def create(
        db: AsyncSession,
        project_id: uuid.UUID,
        org_id: uuid.UUID,
        name: str,
        color: str | None = None,
        position: int = 0
    ) -> ProjectStatusModel:
        status_model = ProjectStatusModel(
            project_id=project_id,
            org_id=org_id,
            name=name,
            color=color,
            position=position
        )
        db.add(status_model)
        await db.flush()
        return status_model
