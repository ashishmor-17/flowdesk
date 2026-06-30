import uuid

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.enums import UserRole
from app.core.errors import ErrorCode
from app.models.users import User
from app.models.org_members import OrgMember
from app.schemas.organization import *
from app.services import org_service
from app.api.deps import (
    get_current_user,
    get_current_org_id,
    get_org_member,
    invite_rate_limiter
)

router = APIRouter(prefix="/org", tags= ["organizations"])

@router.post("/create", response_model= OrganizationResponse, status_code= status.HTTP_201_CREATED)
async def create_org(
    payload: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession  = Depends(get_db)
):
    return await org_service.create_organization(
        db=db,
        org_in=payload,
        creator_id=current_user.id
    )

@router.post(
    "/invite-user", 
    response_model= InvitationResponse,
    status_code= status.HTTP_201_CREATED,
    dependencies= [Depends(invite_rate_limiter)]
)
async def invite_user(
    payload: InvitationCreate,
    org_id: uuid.UUID = Depends(get_current_org_id),
    caller_member: OrgMember = Depends(get_org_member),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if caller_member.role not in [UserRole.ADMIN, UserRole.OWNER]:
        raise HTTPException(
            status_code= status.HTTP_403_FORBIDDEN,
            detail={
                "code": ErrorCode.FORBIDDEN,
                "message": "Only organizations Owner and Admins can invite users."
            }
        )
    
    invitation = await org_service.create_invitation(
        db=db,
        org_id=org_id,
        invited_by=current_user.id,
        email=payload.email,
        role=payload.role
    )

    return InvitationResponse(
        invitation_id= invitation.id,
        invited_email= invitation.invited_email,
        expires_at= invitation.expires_at
    )

@router.post("/accept-invite", response_model= AcceptInviteResponse, status_code= status.HTTP_200_OK)
async def accept_invite(
    payload: AcceptInviteRequest,
    db: AsyncSession = Depends(get_db)
):
    invitation = await org_service.accept_invitation(db, payload.token)

    return AcceptInviteResponse(
        message= "Joined organization successfully.",
        org_id= invitation.org_id,
        role= invitation.role.upper()
    )

@router.get("/members", response_model= OrgMembersListResponse, status_code= status.HTTP_200_OK)
async def list_members(
    org_id: uuid.UUID = Depends(get_current_org_id),
    caller_member: OrgMember = Depends(get_org_member),
    db: AsyncSession = Depends(get_db)
):
    
    members = await org_service.get_org_members(db, org_id)

    def get_full_name(user: User) -> str:
        if user.last_name:
            return f"{user.first_name} {user.last_name}"
        return user.first_name
    
    return OrgMembersListResponse(
        members= [
            OrgMemberResponse(
                user_id=m.user_id,
                full_name=get_full_name(m.user),
                email=m.user.email,
                role=m.role.upper(),
                joined_at=m.joined_at
            )
            for m in members
        ]
    )

@router.delete("/members/{user_id}", status_code= status.HTTP_200_OK)
async def delete_member(
    user_id: uuid.UUID,
    org_id: uuid.UUID = Depends(get_current_org_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    
    await org_service.remove_org_member(
        db=db,
        org_id=org_id,
        caller_id=current_user.id,
        user_to_remove_id=user_id
    )

    return {"message": "Member removed."}

@router.delete("", status_code=status.HTTP_200_OK)
async def delete_org(
    org_id: uuid.UUID = Depends(get_current_org_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await org_service.delete_organization(
        db=db,
        org_id=org_id,
        caller_id=current_user.id
    )
    return {"message": "Organization deleted successfully."}
