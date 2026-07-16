import uuid
import re
import unicodedata
import secrets
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.models.organizations import Organization
from app.models.org_members import OrgMember
from app.models.invitations import Invitation
from app.core.enums import UserRole, InvitationStatus, NotificationType, NotificationEntityType
from app.core.errors import ErrorCode
from app.core.database import transaction_scope
from app.core.redis import redis_client
from app.schemas.organization import OrganizationCreate
from app.services.notification_service import NotificationService
from app.repositories.org_repository import OrgRepository
from app.repositories.user_repository import UserRepository
from app.services.email_service import send_invitation_email

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
                existing = await OrgRepository.get_by_slug(db, slug)
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail={
                            "code": ErrorCode.SLUG_TAKEN,
                            "message": "Organization slug is already taken"
                        }
                    )
            else:
                existing_slugs = await OrgRepository.get_existing_slugs(db, base_slug)
                existing_set = set(existing_slugs)

                slug = base_slug
                counter = 1
                while slug in existing_set:
                    slug = f"{base_slug}-{counter}"
                    counter += 1

            org = await OrgRepository.create_organization(db, name=org_in.name, slug=slug, creator_id=creator_id)
            await OrgRepository.create_member(db, org_id=org.id, user_id=creator_id, role=UserRole.OWNER)
            
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
        existing_member = await OrgRepository.get_member_by_email(db, org_id, email)
        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": ErrorCode.ALREADY_MEMBER,
                    "message": "This email is already a member of this organziation."
                }
            )
        
        token = secrets.token_urlsafe(32)
        invitation = await OrgRepository.create_invitation(
            db,
            org_id=org_id,
            invited_by=invited_by,
            invited_email=email,
            role=role,
            token=token,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )

        org = await OrgRepository.get_by_id(db, org_id)
        inviter_user = await UserRepository.get_by_id(db, invited_by)
        inviter_name = inviter_user.full_name or inviter_user.email if inviter_user else "Someone"
        org_name = org.name if org else "an Organization"

        try:
            await send_invitation_email(
                recipient=email,
                org_name=org_name,
                inviter_name=inviter_name,
                role=role.value if hasattr(role, "value") else str(role),
                token=token
            )
        except Exception as e:
            logger.error(f"Failed to send invitation email: {e}")

        invited_user = await UserRepository.get_by_email(db, email)
        if invited_user:
            NotificationService.create_notification(
                org_id=org_id,
                recipient_id=invited_user.id,
                type=NotificationType.ORG_INVITE,
                actor_id=invited_by,
                entity_type=NotificationEntityType.INVITATION,
                entity_id=invitation.id,
                payload={
                    "invitation_id": str(invitation.id),
                    "org_name": org_name,
                    "invited_by_name": inviter_name,
                    "token": token
                }
            )

        return invitation
        
async def accept_invitation(db: AsyncSession, token: str) -> Invitation:
    async with transaction_scope(db):
        invitation = await OrgRepository.get_invitation_by_token(db, token)
        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": ErrorCode.INVITE_NOT_FOUND,
                    "message": "Invitation not found."
                }
            )
        
        now = datetime.now(invitation.expires_at.tzinfo) if invitation.expires_at.tzinfo else datetime.utcnow()

        if invitation.status != InvitationStatus.PENDING or invitation.expires_at < now:
            if invitation.status == InvitationStatus.PENDING:
                invitation.status = InvitationStatus.EXPIRED

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": ErrorCode.INVITE_EXPIRED,
                    "message": "This invitation has expired or has already been accepted."
                }
            )
        
        user = await UserRepository.get_by_email(db, invitation.invited_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "USER_NOT_REGISTERED",
                    "message": "Please register an account with your invited email before accepting."
                }
            )
        
        existing_member = await OrgRepository.get_member(db, invitation.org_id, user.id)
        if existing_member:
            invitation.status = InvitationStatus.ACCEPTED
            return invitation
        
        await OrgRepository.create_member(db, org_id=invitation.org_id, user_id=user.id, role=invitation.role)

        cache_key = f"org:{invitation.org_id}:members"
        await redis_client.delete(cache_key)

        invitation.status = InvitationStatus.ACCEPTED
        return invitation
    
async def get_org_members(db: AsyncSession, org_id: uuid.UUID) -> list[OrgMember]:
    return await OrgRepository.list_members(db, org_id)

async def remove_org_member(
        db: AsyncSession,
        org_id: uuid.UUID,
        caller_id: uuid.UUID,
        user_to_remove_id: uuid.UUID
) -> None:
    async with transaction_scope(db):
        caller = await OrgRepository.get_member(db, org_id, caller_id)
        if not caller or caller.role not in [UserRole.ADMIN, UserRole.OWNER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": ErrorCode.FORBIDDEN,
                    "message": "Only organization Owner and Admins can remove members."
                }
            )
        
        target = await OrgRepository.get_member(db, org_id, user_to_remove_id)
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "MEMBER_NOT_FOUND",
                    "message": "User is not a member of this organization."
                }
            )
        
        if caller.role == UserRole.ADMIN and target.role == UserRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": ErrorCode.FORBIDDEN,
                    "message": "Admins can not remove owners."
                }
            )
        
        if target.role == UserRole.OWNER:
            owner_count = await OrgRepository.get_owner_count(db, org_id)
            if owner_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "CANNOT_REMOVE_LAST_OWNER",
                        "message": "The organization must have atleast one owner."
                    }
                )
            
        await OrgRepository.delete_member(db, target)
        cache_key = f"org:{org_id}:members"
        await redis_client.delete(cache_key)

async def delete_organization(
    db: AsyncSession,
    org_id: uuid.UUID,
    caller_id: uuid.UUID
) -> None:
    async with transaction_scope(db):
        caller = await OrgRepository.get_member(db, org_id, caller_id)
        if not caller or caller.role != UserRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": ErrorCode.FORBIDDEN,
                    "message": "Only the organization Owner can delete the organization."
                }
            )

        org = await OrgRepository.get_by_id(db, org_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ORGANIZATION_NOT_FOUND",
                    "message": "Organization not found."
                }
            )

        await OrgRepository.delete_organization(db, org)

async def update_member_role(
    db: AsyncSession,
    org_id: uuid.UUID,
    caller_id: uuid.UUID,
    user_id: uuid.UUID,
    new_role: UserRole,
    action_for_prev_owner: str = "admin"
) -> OrgMember | None:
    async with transaction_scope(db):
        caller = await OrgRepository.get_member(db, org_id, caller_id)
        if not caller or caller.role != UserRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": ErrorCode.FORBIDDEN,
                    "message": "Only the organization Owner can change member roles."
                }
            )

        target = await OrgRepository.get_member(db, org_id, user_id)
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "MEMBER_NOT_FOUND",
                    "message": "Target user is not a member of this organization."
                }
            )

        if caller_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "BAD_REQUEST",
                    "message": "An owner cannot change their own role directly. Transfer ownership instead."
                }
            )

        # Normalize new role to enum
        role_enum = UserRole(new_role)

        if role_enum == UserRole.OWNER:
            # Promote target to OWNER
            target.role = UserRole.OWNER
            
            # Action for current owner (caller)
            if action_for_prev_owner == "leave":
                await OrgRepository.delete_member(db, caller)
            else:
                caller.role = UserRole.ADMIN
        else:
            # If target is owner and being demoted, ensure we have other owners
            if target.role == UserRole.OWNER:
                owner_count = await OrgRepository.get_owner_count(db, org_id)
                if owner_count <= 1:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "code": "CANNOT_DEMOTE_LAST_OWNER",
                            "message": "The organization must have at least one owner."
                        }
                    )
            target.role = role_enum

        cache_key = f"org:{org_id}:members"
        await redis_client.delete(cache_key)

        # Create notification for target user
        try:
            actor_user = await UserRepository.get_by_id(db, caller_id)
            actor_name = actor_user.full_name or actor_user.email if actor_user else "System"
            org_obj = await OrgRepository.get_by_id(db, org_id)
            org_name = org_obj.name if org_obj else "Organization"

            NotificationService.create_notification(
                org_id=org_id,
                recipient_id=user_id,
                type=NotificationType.ROLE_CHANGED,
                actor_id=caller_id,
                entity_type=NotificationEntityType.ORGANIZATION,
                entity_id=org_id,
                payload={
                    "org_name": org_name,
                    "new_role": role_enum.value.upper(),
                    "updated_by_name": actor_name
                }
            )
        except Exception as e:
            logger.error(f"Failed to create role change notification: {e}")

        return target
