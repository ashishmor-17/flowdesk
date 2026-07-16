import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.teams import Team
from app.models.team_members import TeamMember

class TeamRepository:
    @staticmethod
    async def get_by_id(db: AsyncSession, team_id: uuid.UUID, org_id: uuid.UUID) -> Team | None:
        return await db.scalar(
            select(Team).where(Team.id == team_id, Team.org_id == org_id)
        )

    @staticmethod
    async def get_by_name(db: AsyncSession, name: str, org_id: uuid.UUID) -> Team | None:
        return await db.scalar(
            select(Team).where(Team.name == name, Team.org_id == org_id)
        )

    @staticmethod
    async def create(db: AsyncSession, org_id: uuid.UUID, name: str) -> Team:
        team = Team(org_id=org_id, name=name)
        db.add(team)
        await db.flush()
        return team

    @staticmethod
    async def delete(db: AsyncSession, team: Team) -> None:
        await db.delete(team)

    @staticmethod
    async def get_member(db: AsyncSession, team_id: uuid.UUID, user_id: uuid.UUID) -> TeamMember | None:
        return await db.scalar(
            select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        )

    @staticmethod
    async def add_member(db: AsyncSession, team_id: uuid.UUID, user_id: uuid.UUID) -> TeamMember:
        member = TeamMember(team_id=team_id, user_id=user_id)
        db.add(member)
        await db.flush()
        return member

    @staticmethod
    async def remove_member(db: AsyncSession, member: TeamMember) -> None:
        await db.delete(member)

    @staticmethod
    async def list_member_ids(db: AsyncSession, team_id: uuid.UUID) -> list[uuid.UUID]:
        result = await db.scalars(
            select(TeamMember.user_id).where(TeamMember.team_id == team_id)
        )
        return list(result.all())

    @staticmethod
    async def list_org_teams(db: AsyncSession, org_id: uuid.UUID) -> list[Team]:
        result = await db.scalars(
            select(Team).where(Team.org_id == org_id)
        )
        return list(result.all())

