import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import transaction_scope
from app.models.teams import Team
from app.models.team_members import TeamMember
from app.models.org_members import OrgMember
from app.repositories.team_repository import TeamRepository
from app.repositories.org_repository import OrgRepository
from app.schemas.teams import TeamCreate, TeamMemberAdd

async def create_team(
    db: AsyncSession,
    payload: TeamCreate,
    org_member: OrgMember
) -> Team:
    if org_member.role.lower() not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Org Admin or Owner can create teams."
        )

    existing = await TeamRepository.get_by_name(db, payload.name, org_member.org_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Team name already exists in this organization."
        )

    async with transaction_scope(db):
        return await TeamRepository.create(db, org_member.org_id, payload.name)

async def add_team_member(
    db: AsyncSession,
    team_id: uuid.UUID,
    payload: TeamMemberAdd,
    org_member: OrgMember
) -> TeamMember:
    if org_member.role.lower() not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Org Admin or Owner can add members to teams."
        )

    team = await TeamRepository.get_by_id(db, team_id, org_member.org_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found in this organization."
        )

    user_is_org_member = await OrgRepository.get_member(db, org_member.org_id, payload.user_id)
    if not user_is_org_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a member of this organization."
        )

    already_member = await TeamRepository.get_member(db, team_id, payload.user_id)
    if already_member:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this team."
        )

    async with transaction_scope(db):
        return await TeamRepository.add_member(db, team_id, payload.user_id)

async def remove_team_member(
    db: AsyncSession,
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    org_member: OrgMember
) -> None:
    if org_member.role.lower() not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Org Admin or Owner can remove members from teams."
        )

    team = await TeamRepository.get_by_id(db, team_id, org_member.org_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found in this organization."
        )

    membership = await TeamRepository.get_member(db, team_id, user_id)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of this team."
        )

    async with transaction_scope(db):
        await TeamRepository.remove_member(db, membership)

async def delete_team(
    db: AsyncSession,
    team_id: uuid.UUID,
    org_member: OrgMember
) -> None:
    if org_member.role.lower() not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Org Admin or Owner can delete teams."
        )

    team = await TeamRepository.get_by_id(db, team_id, org_member.org_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found in this organization."
        )

    async with transaction_scope(db):
        await TeamRepository.delete(db, team)

async def list_teams(
    db: AsyncSession,
    org_member: OrgMember
) -> list[dict]:
    
    teams = await TeamRepository.list_org_teams(db, org_member.org_id)
    team_details = []
    for team in teams:
        member_ids = await TeamRepository.list_member_ids(db, team.id)
        team_details.append({
            "id": team.id,
            "org_id": team.org_id,
            "name": team.name,
            "created_at": team.created_at,
            "member_ids": member_ids
        })
    return team_details

