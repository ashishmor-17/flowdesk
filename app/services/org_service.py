import uuid
import re
import unicodedata
import secrets
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from contextlib import asynccontextmanager

from app.models.users import User
from app.models.organizations import Organization
from app.models.org_members import OrgMember
from app.models.invitations import Invitation
from app.core.enums import UserRole, InvitationStatus, NotificationType, NotificationEntityType
from app.core.errors import ErrorCode
from app.core.database import transaction_scope
from app.schemas.organization import OrganizationCreate
from app.services.notification_service import NotificationService

def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")

async def create_organization(
    db: AsyncSession,
    org_in: OrganizationCreate,
    creator_id: uuid.UUID
) -> Organization:
    base_slug = slugify(org_in.slug or org_in.name)
    if not base_slug:
        base_slug = str(uuid.uuid4())[:8]

    try:
        async with transaction_scope(db):
            if org_in.slug:
                slug = base_slug
                existing = await db.scalar(
                    select(Organization).where(Organization.slug == slug)
                )
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail={
                            "code": ErrorCode.SLUG_TAKEN,
                            "message": "Organization slug is already taken"
                        }
                    )
            else:
                existing_slugs = await db.scalars(
                    select(Organization.slug).where(
                        func.regexp_match(Organization.slug, f"^{base_slug}(-[0-9]+)?$") != None
                    )
                )
                existing_set = set(existing_slugs.all())

                slug = base_slug
                counter = 1
                while slug in existing_set:
                    slug = f"{base_slug}-{counter}"
                    counter += 1

            org = Organization(
                name=org_in.name,
                slug=slug,
                created_by=creator_id
            )
            db.add(org)
            await db.flush()

            member = OrgMember(
                org_id=org.id,
                user_id=creator_id,
                role=UserRole.OWNER
            )
            db.add(member)
            
            return org

    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": ErrorCode.SLUG_TAKEN,
                "message": "Organization slug is already taken"
            }
        )

async def create_invitation(
        db: AsyncSession,
        org_id: uuid.UUID,
        invited_by: uuid.UUID,
        email: str,
        role: UserRole
) -> Invitation:
    
    async with transaction_scope(db):

        existing_member = await db.scalar(
            select(OrgMember)
            .join(User)
            .where(OrgMember.org_id == org_id, User.email == email)
        )

        if existing_member:
            raise HTTPException(
                status_code= status.HTTP_409_CONFLICT,
                detail={
                    "code": ErrorCode.ALREADY_MEMBER,
                    "message": "This email is already a member of this organziation."
                }
            )
        
        token = secrets.token_urlsafe(32)

        invitation = Invitation(
            org_id= org_id,
            invited_email= email,
            invited_by=invited_by,
            token=token,
            role=role,
            status=InvitationStatus.PENDING,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )

        db.add(invitation)
        await db.flush()

        invited_user = await db.scalar(
            select(User).where(User.email == email)
        )
        if invited_user:
            inviter_user = await db.get(User, invited_by)
            inviter_name = f"{inviter_user.first_name} {inviter_user.last_name}" if inviter_user.last_name else inviter_user.first_name
            org = await db.get(Organization, org_id)
            NotificationService.create_notification(
                org_id=org_id,
                recipient_id=invited_user.id,
                type=NotificationType.ORG_INVITE,
                actor_id=invited_by,
                entity_type=NotificationEntityType.INVITATION,
                entity_id=invitation.id,
                payload={
                    "invitation_id": str(invitation.id),
                    "org_name": org.name,
                    "invited_by_name": inviter_name
                }
            )

        return invitation
        
async def accept_invitation(db:AsyncSession, token: str) -> Invitation:
    
    async with transaction_scope(db):
        invitation = await db.scalar(
            select(Invitation)
            .where(Invitation.token == token)
        )

        if not invitation:
            raise HTTPException(
                status_code= status.HTTP_404_NOT_FOUND,
                detail= {
                    "code": ErrorCode.INVITE_NOT_FOUND,
                    "message": "Invitation not found."
                }
            )
        
        now = datetime.now(invitation.expires_at.tzinfo) if invitation.expires_at.tzinfo else datetime.utcnow()

        if invitation.status != InvitationStatus.PENDING or invitation.expires_at < now:
            if invitation.status == InvitationStatus.PENDING:
                invitation.status = InvitationStatus.EXPIRED

            raise HTTPException(
                status_code= status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": ErrorCode.INVITE_EXPIRED,
                    "message": "This invitation has expired or has already been accepted."
                }
            )
        
        user = await db.scalar(
            select(User)
            .where(User.email == invitation.invited_email)
        )

        if not user:
            raise HTTPException(
                status_code= status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "USER_NOT_REGISTERED",
                    "message": "Please register an account with your invited email before accepting."
                }
            )
        
        existing_member = await db.scalar(
            select(OrgMember)
            .where(
                OrgMember.org_id == invitation.org_id,
                OrgMember.user_id == user.id
            )
        )

        if existing_member:
            invitation.status = InvitationStatus.ACCEPTED
            return invitation
        
        member = OrgMember(
            org_id=invitation.org_id,
            user_id=user.id,
            role=invitation.role
        )

        db.add(member)
        await db.flush()

        invitation.status = InvitationStatus.ACCEPTED
        return invitation
    
async def get_org_members(db: AsyncSession, org_id: uuid.UUID) -> list[OrgMember]:

    result = await db.scalars(
        select(OrgMember)
        .options(selectinload(OrgMember.user))
        .where(OrgMember.org_id == org_id)
    )

    return list(result.all())

async def remove_org_member(
        db: AsyncSession,
        org_id: uuid.UUID,
        caller_id: uuid.UUID,
        user_to_remove_id: uuid.UUID
) -> None:
    
    async with transaction_scope(db):
        caller = await db.scalar(
            select(OrgMember)
            .where(OrgMember.org_id == org_id,
                   OrgMember.user_id == caller_id
            )
        )

        if not caller or caller.role not in [UserRole.ADMIN, UserRole.OWNER]:
            raise HTTPException(
                status_code= status.HTTP_403_FORBIDDEN,
                detail= {
                    "code": ErrorCode.FORBIDDEN,
                    "message" : "Only organization Owner and Admins can remove members."
                }
            )
        
        target = await db.scalar(
            select(OrgMember)
            .where(
                OrgMember.org_id == org_id,
                OrgMember.user_id == user_to_remove_id
            )
        )

        if not target:
            raise HTTPException(
                status_code= status.HTTP_404_NOT_FOUND,
                detail= {
                    "code": "MEMBER_NOT_FOUND",
                    "message": "User is not a member of this organization."
                }
            )
        
        if caller.role == UserRole.ADMIN and target.role == UserRole.OWNER:
            raise HTTPException(
                status_code= status.HTTP_403_FORBIDDEN,
                detail= {
                    "code": ErrorCode.FORBIDDEN,
                    "message": "Admins can not remove owners."
                }
            )
        
        if target.role == UserRole.OWNER:
            owner_count = await db.scalar(
                select(func.count(OrgMember.id))
                .where(OrgMember.org_id == org_id, OrgMember.role == UserRole.OWNER)
            )

            if owner_count <=1 :
                raise HTTPException(
                    status_code= status.HTTP_400_BAD_REQUEST,
                    detail= {
                        "code": "CANNOT_REMOVE_LAST_OWNER",
                        "message": "The organization must have atleast one owner."
                    }
                )
            
        await db.delete(target)

async def delete_organization(
    db: AsyncSession,
    org_id: uuid.UUID,
    caller_id: uuid.UUID
) -> None:
    
    async with transaction_scope(db):
        caller = await db.scalar(
            select(OrgMember).where(
                OrgMember.org_id == org_id,
                OrgMember.user_id == caller_id
            )
        )
        if not caller or caller.role != UserRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": ErrorCode.FORBIDDEN,
                    "message": "Only the organization Owner can delete the organization."
                }
            )

        org = await db.scalar(
            select(Organization).where(Organization.id == org_id)
        )
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ORGANIZATION_NOT_FOUND",
                    "message": "Organization not found."
                }
            )

        await db.delete(org)
