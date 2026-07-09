import uuid
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.organizations import Organization
from app.models.org_members import OrgMember
from app.models.invitations import Invitation
from app.models.users import User
from app.core.enums import UserRole, InvitationStatus

class OrgRepository:
    @staticmethod
    async def get_by_slug(db: AsyncSession, slug: str) -> Organization | None:
        return await db.scalar(
            select(Organization).where(Organization.slug == slug)
        )

    @staticmethod
    async def get_existing_slugs(db: AsyncSession, base_slug: str) -> list[str]:
        result = await db.scalars(
            select(Organization.slug).where(
                func.regexp_match(Organization.slug, f"^{base_slug}(-[0-9]+)?$") != None
            )
        )
        return list(result.all())

    @staticmethod
    async def create_organization(
        db: AsyncSession,
        *,
        name: str,
        slug: str,
        creator_id: uuid.UUID
    ) -> Organization:
        org = Organization(name=name, slug=slug, created_by=creator_id)
        db.add(org)
        await db.flush()
        return org

    @staticmethod
    async def create_member(
        db: AsyncSession,
        *,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        role: UserRole
    ) -> OrgMember:
        member = OrgMember(org_id=org_id, user_id=user_id, role=role)
        db.add(member)
        await db.flush()
        return member

    @staticmethod
    async def get_member(
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> OrgMember | None:
        return await db.scalar(
            select(OrgMember)
            .where(OrgMember.org_id == org_id, OrgMember.user_id == user_id)
            .options(selectinload(OrgMember.user))
        )

    @staticmethod
    async def get_member_by_email(
        db: AsyncSession,
        org_id: uuid.UUID,
        email: str
    ) -> OrgMember | None:
        return await db.scalar(
            select(OrgMember)
            .join(User)
            .where(OrgMember.org_id == org_id, User.email == email)
        )

    @staticmethod
    async def list_members(db: AsyncSession, org_id: uuid.UUID) -> list[OrgMember]:
        result = await db.scalars(
            select(OrgMember)
            .where(OrgMember.org_id == org_id)
            .options(selectinload(OrgMember.user))
        )
        return list(result.all())

    @staticmethod
    async def get_owner_count(db: AsyncSession, org_id: uuid.UUID) -> int:
        return await db.scalar(
            select(func.count(OrgMember.id))
            .where(OrgMember.org_id == org_id, OrgMember.role == UserRole.OWNER)
        )

    @staticmethod
    async def create_invitation(
        db: AsyncSession,
        *,
        org_id: uuid.UUID,
        invited_by: uuid.UUID,
        invited_email: str,
        role: UserRole,
        token: str,
        expires_at: datetime
    ) -> Invitation:
        invitation = Invitation(
            org_id=org_id,
            invited_by=invited_by,
            invited_email=invited_email,
            role=role,
            token=token,
            expires_at=expires_at
        )
        db.add(invitation)
        await db.flush()
        return invitation

    @staticmethod
    async def get_invitation_by_email_and_org(
        db: AsyncSession,
        email: str,
        org_id: uuid.UUID
    ) -> Invitation | None:
        return await db.scalar(
            select(Invitation).where(
                Invitation.invited_email == email,
                Invitation.org_id == org_id,
                Invitation.status == InvitationStatus.PENDING
            )
        )

    @staticmethod
    async def get_invitation_by_token(db: AsyncSession, token: str) -> Invitation | None:
        return await db.scalar(
            select(Invitation).where(Invitation.token == token)
        )

    @staticmethod
    async def get_by_id(db: AsyncSession, org_id: uuid.UUID) -> Organization | None:
        return await db.get(Organization, org_id)

    @staticmethod
    async def delete_organization(db: AsyncSession, org: Organization) -> None:
        await db.delete(org)

    @staticmethod
    async def delete_member(db: AsyncSession, member: OrgMember) -> None:
        await db.delete(member)
